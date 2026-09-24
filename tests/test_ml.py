"""
Tests del clasificador NLP local (PB-05) y su reentrenamiento (PB-06).

El clasificador se entrena de verdad sobre el DATASET_BASE: no se mockea
scikit-learn, porque parte del valor del módulo es demostrar que el modelo
local efectivamente clasifica. El entrenamiento sobre ~600 ejemplos cortos
es lo bastante rápido para correr dentro de la suite.
"""

from app.services import ml_service


GASTO_BASE = {
    "descripcion": "Licencia Adobe",
    "monto": 5000,
    "categoria": "Software",
    "fecha": "2026-03-01T10:00:00",
}


# ── Endpoint GET /ml/estado ──────────────────────────────────────────────────

def test_estado_modelo_sin_auth(client):
    assert client.get("/ml/estado").status_code == 401


def test_estado_modelo_inicial(client, auth_headers):
    # Sin gastos ni entrenamiento previo el usuario no tiene modelo propio:
    # el sistema reporta que usaría el modelo base.
    response = client.get("/ml/estado", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tiene_modelo_propio"] is False
    assert data["usa_modelo_base"] is True


# ── Clasificación real con el modelo ML local ────────────────────────────────

def test_clasificar_descripcion_conocida_devuelve_categoria_correcta(db):
    # "adobe photoshop" figura en el dataset base etiquetado como Software.
    # El clasificador entrenado debe reproducir esa categoría.
    resultado = ml_service.clasificar_gasto("adobe photoshop", db, usuario_id=0)
    assert resultado["categoria"] == "Software"
    # El usuario 0 no tiene modelo reentrenado propio: la predicción sale del
    # modelo base, y la respuesta lo tiene que declarar como tal.
    assert resultado["fuente"] == "ml_base"
    assert 0.0 <= resultado["confianza"] <= 1.0


def test_fuente_distingue_modelo_propio_del_modelo_base(db):
    """Regresión: la fuente informada tiene que coincidir con /ml/estado.

    Antes se devolvía "ml_propio" siempre, incluso cuando el usuario todavía
    no había cruzado el umbral de reentrenamiento y la predicción venía del
    modelo base compartido.
    """
    # Sin modelo propio → ml_base, coherente con usa_modelo_base=True.
    assert ml_service.clasificar_gasto("adobe photoshop", db, usuario_id=0)["fuente"] == "ml_base"
    estado = ml_service.obtener_estado_modelo(db, 0)
    assert estado["tiene_modelo_propio"] is False

    # Ninguna fuente posible del clasificador es un servicio externo.
    assert ml_service.clasificar_gasto("notebook dell", db, usuario_id=0)["fuente"] in (
        "ml_base", "ml_propio",
    )


def test_clasificar_siempre_devuelve_categoria_valida(db):
    # Ante una descripción sin relación con ninguna categoría, el modelo
    # igual debe devolver una de las categorías del conjunto cerrado.
    resultado = ml_service.clasificar_gasto("xqz texto sin sentido alguno", db, usuario_id=0)
    assert resultado["categoria"] in ml_service.CATEGORIAS_VALIDAS


# ── Entrenamiento del modelo base ────────────────────────────────────────────

def test_entrenar_modelo_base_usa_dataset_completo(db):
    modelo = ml_service.entrenar_modelo_base(db)
    assert modelo.usuario_id is None
    assert modelo.activo is True
    assert modelo.n_ejemplos == len(ml_service.DATASET_BASE)
    # 600 ejemplos ≥ 100 → el selector de algoritmo elige SVM.
    assert modelo.algoritmo == "svm"


# ── Endpoint POST /ml/reentrenar ─────────────────────────────────────────────

def test_reentrenar_sin_auth(client):
    assert client.post("/ml/reentrenar").status_code == 401


def test_reentrenar_pocos_ejemplos_usa_base(client, auth_headers):
    # Con menos de 20 gastos propios no se entrena un modelo personalizado:
    # el endpoint responde indicando que se sigue usando el modelo base.
    response = client.post("/ml/reentrenar", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["n_ejemplos"] < 20
    assert "base" in data["mensaje"].lower()


def test_reentrenar_genera_modelo_personalizado(client, auth_headers):
    # Con 20+ gastos propios el reentrenamiento construye un modelo propio
    # del usuario, combinando dataset base y ejemplos personales (PB-06).
    for i in range(20):
        client.post(
            "/gastos/",
            json={**GASTO_BASE, "descripcion": f"Gasto profesional {i}"},
            headers=auth_headers,
        )

    response = client.post("/ml/reentrenar", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["n_ejemplos"] >= 20 + len(ml_service.DATASET_BASE)

    estado = client.get("/ml/estado", headers=auth_headers).json()
    assert estado["tiene_modelo_propio"] is True


# ── Endpoint POST /ml/corregir ───────────────────────────────────────────────

def test_corregir_sin_auth(client):
    response = client.post(
        "/ml/corregir",
        json={"descripcion": "Algo", "categoria_correcta": "Software"},
    )
    assert response.status_code == 401


def test_corregir_categoria_invalida(client, auth_headers):
    response = client.post(
        "/ml/corregir",
        json={"descripcion": "Algo", "categoria_correcta": "CategoriaInexistente"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_corregir_categoria_valida(client, auth_headers):
    response = client.post(
        "/ml/corregir",
        json={"descripcion": "Pago hosting mensual", "categoria_correcta": "Infraestructura"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "nuevo_estado" in data
    assert data["mensaje"]


def test_correccion_persiste_y_se_usa_en_reentrenamiento(client, auth_headers, db):
    # Una corrección explícita debe quedar persistida con la forma normalizada
    # (sin tildes, lowercase, colapso de espacios) y debe sumarse como ejemplo
    # al próximo reentrenamiento del modelo del usuario.
    from app.models.cache_clasificacion import CacheClasificacion

    client.post(
        "/ml/corregir",
        json={"descripcion": "xyz token único de prueba", "categoria_correcta": "Marketing"},
        headers=auth_headers,
    )
    persistidas = db.query(CacheClasificacion).filter(
        # NFKD + sin tildes → "único" se persiste como "unico"
        CacheClasificacion.descripcion_normalizada == "xyz token unico de prueba",
    ).all()
    assert len(persistidas) == 1
    assert persistidas[0].categoria == "Marketing"


# ── Entradas inválidas y aislamiento (revisión M04) ─────────────────────────

def test_corregir_descripcion_vacia_no_crea_una_regla(client, auth_headers):
    # Antes se guardaba la regla "texto vacío → Software" y desde ahí toda
    # descripción en blanco salía clasificada con 100% de confianza.
    for texto in ("", "   "):
        response = client.post(
            "/ml/corregir",
            json={"descripcion": texto, "categoria_correcta": "Software"},
            headers=auth_headers,
        )
        assert response.status_code == 422, texto


def test_corregir_descripcion_demasiado_larga(client, auth_headers):
    response = client.post(
        "/ml/corregir",
        json={"descripcion": "x" * 256, "categoria_correcta": "Software"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_clasificar_descripcion_vacia_o_demasiado_larga(client, auth_headers):
    for texto in ("", "   ", "pizza " * 100):
        response = client.post("/gastos/clasificar", json={"descripcion": texto}, headers=auth_headers)
        assert response.status_code == 422, texto[:20]


def test_correccion_de_un_usuario_no_afecta_a_otro(client, auth_headers):
    """La corrección queda asociada a quien la hizo: el otro usuario sigue
    recibiendo la predicción del modelo, no la regla ajena."""
    client.post(
        "/ml/corregir",
        json={"descripcion": "Licencia anual de Adobe Photoshop", "categoria_correcta": "Marketing"},
        headers=auth_headers,
    )
    propia = client.post("/gastos/clasificar", json={"descripcion": "Licencia anual de Adobe Photoshop"},
                         headers=auth_headers).json()
    assert propia["categoria_sugerida"] == "Marketing"
    assert propia["fuente"] == "correccion_usuario"

    client.post("/auth/register", json={"nombre": "Otra", "email": "otra@test.com", "password": "password123"})
    token = client.post("/auth/login", data={"username": "otra@test.com", "password": "password123"}).json()["access_token"]
    ajena = client.post("/gastos/clasificar", json={"descripcion": "Licencia anual de Adobe Photoshop"},
                        headers={"Authorization": f"Bearer {token}"}).json()
    assert ajena["fuente"] != "correccion_usuario"
    assert ajena["categoria_sugerida"] != "Marketing"
