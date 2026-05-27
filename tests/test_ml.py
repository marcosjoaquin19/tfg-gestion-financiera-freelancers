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
    assert resultado["fuente"] == "ml_propio"
    assert 0.0 <= resultado["confianza"] <= 1.0


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
