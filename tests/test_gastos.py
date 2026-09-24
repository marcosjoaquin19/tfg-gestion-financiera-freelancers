"""
Tests del módulo de Gastos (/gastos).

Verifican el CRUD de gastos, las validaciones, la clasificación automática y la
detección de duplicados al crear un gasto, y el aislamiento por usuario.
"""

from app.services.ml_service import CATEGORIAS_VALIDAS

GASTO_BASE = {
    "descripcion": "Suscripción Adobe",
    "monto": 5000,
    "categoria": "Software",
    "fecha": "2026-03-01T10:00:00"
}


def test_crear_gasto(client, auth_headers):
    response = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["monto"] == GASTO_BASE["monto"]
    assert data["es_duplicado"] is False


def test_crear_gasto_sin_auth(client):
    response = client.post("/gastos/", json=GASTO_BASE)
    assert response.status_code == 401


def test_crear_gasto_monto_negativo(client, auth_headers):
    response = client.post("/gastos/", json={**GASTO_BASE, "monto": -100}, headers=auth_headers)
    assert response.status_code == 422


def test_listar_gastos(client, auth_headers):
    client.post("/gastos/", json=GASTO_BASE, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "descripcion": "Hosting"}, headers=auth_headers)
    response = client.get("/gastos/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_listar_gastos_filtro_categoria(client, auth_headers):
    client.post("/gastos/", json=GASTO_BASE, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "categoria": "Marketing"}, headers=auth_headers)
    response = client.get("/gastos/?categoria=Marketing", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_listar_gastos_solo_duplicados(client, auth_headers):
    # al crear gastos nuevos no hay duplicados todavía
    client.post("/gastos/", json=GASTO_BASE, headers=auth_headers)
    response = client.get("/gastos/?solo_duplicados=true", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_obtener_gasto(client, auth_headers):
    creado = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    response = client.get(f"/gastos/{creado['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == creado["id"]


def test_obtener_gasto_inexistente(client, auth_headers):
    response = client.get("/gastos/9999", headers=auth_headers)
    assert response.status_code == 404


def test_actualizar_gasto(client, auth_headers):
    creado = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    response = client.put(f"/gastos/{creado['id']}", json={**GASTO_BASE, "monto": 9000}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["monto"] == 9000


def test_eliminar_gasto(client, auth_headers):
    creado = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    assert client.delete(f"/gastos/{creado['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/gastos/{creado['id']}", headers=auth_headers).status_code == 404


def test_crear_gasto_sin_categoria_la_infiere_el_clasificador(client, auth_headers):
    """HU-04: se puede registrar un gasto con solo descripción y monto.

    La interfaz siempre manda la categoría (muestra la sugerencia para que el
    usuario la confirme), pero la API tiene que aceptar el alta sin ella y
    resolverla con el clasificador local.
    """
    response = client.post(
        "/gastos/",
        json={
            "descripcion": "Licencia anual de Adobe Photoshop",
            "monto": 42000,
            "fecha": "2026-09-10T10:00:00",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    # No se exige una categoría puntual: se exige que haya inferido una válida
    # del conjunto cerrado, sin que el cliente la mandara.
    assert data["categoria"] in CATEGORIAS_VALIDAS


# ── Validación de datos inválidos (revisión M03) ────────────────────────────
# Antes de estos controles, varios de estos casos llegaban a la base y
# terminaban en un error 500 sin explicación.

def test_crear_gasto_descripcion_vacia(client, auth_headers):
    for texto in ("", "   "):
        response = client.post("/gastos/", json={**GASTO_BASE, "descripcion": texto}, headers=auth_headers)
        assert response.status_code == 422, texto


def test_crear_gasto_descripcion_demasiado_larga(client, auth_headers):
    response = client.post("/gastos/", json={**GASTO_BASE, "descripcion": "x" * 256}, headers=auth_headers)
    assert response.status_code == 422


def test_crear_gasto_monto_fuera_de_rango(client, auth_headers):
    response = client.post("/gastos/", json={**GASTO_BASE, "monto": 10 ** 10}, headers=auth_headers)
    assert response.status_code == 422


def test_crear_gasto_monto_nan_o_infinito(client, auth_headers):
    # Se arma el JSON a mano porque NaN/Infinity no son JSON estándar, pero el
    # decodificador de Python los acepta si alguien los manda.
    for valor in ("NaN", "Infinity"):
        cuerpo = ('{"descripcion": "prueba", "monto": %s, "categoria": "Otros", '
                  '"fecha": "2026-03-01T10:00:00"}' % valor)
        response = client.post(
            "/gastos/", content=cuerpo,
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert response.status_code == 422, valor
    assert client.get("/gastos/", headers=auth_headers).json() == []


def test_crear_gasto_categoria_invalida(client, auth_headers):
    response = client.post("/gastos/", json={**GASTO_BASE, "categoria": "Pizza"}, headers=auth_headers)
    assert response.status_code == 422
    assert "Software" in response.text, "el error lista las categorías válidas"


def test_categoria_invalida_no_llega_al_reentrenamiento(client, auth_headers):
    """Una categoría fuera de las 12 no se guarda, así que nunca puede
    aparecer como clase nueva cuando se reentrena el modelo del usuario."""
    client.post("/gastos/", json={**GASTO_BASE, "categoria": "Pizza"}, headers=auth_headers)
    categorias = {g["categoria"] for g in client.get("/gastos/", headers=auth_headers).json()}
    assert categorias <= set(CATEGORIAS_VALIDAS)


def test_editar_gasto_con_categoria_invalida(client, auth_headers):
    creado = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    response = client.put(f"/gastos/{creado['id']}", json={**GASTO_BASE, "categoria": "Pizza"}, headers=auth_headers)
    assert response.status_code == 422


def test_editar_gasto_sin_categoria_conserva_la_actual(client, auth_headers):
    creado = client.post("/gastos/", json={**GASTO_BASE, "categoria": "Hardware"}, headers=auth_headers).json()
    sin_categoria = {k: v for k, v in GASTO_BASE.items() if k != "categoria"}
    response = client.put(f"/gastos/{creado['id']}", json={**sin_categoria, "monto": 7000}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["categoria"] == "Hardware"
    assert response.json()["monto"] == 7000


# ── La marca de duplicado se mantiene al día al editar y borrar ──────────────

def test_corregir_el_monto_de_un_gasto_duplicado_retira_la_advertencia(client, auth_headers):
    primero = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    segundo = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    assert segundo["es_duplicado"] is True

    corregido = client.put(f"/gastos/{segundo['id']}", json={**GASTO_BASE, "monto": 999}, headers=auth_headers)
    assert corregido.json()["es_duplicado"] is False

    quedo = client.get(f"/gastos/{primero['id']}", headers=auth_headers)
    assert quedo.json()["es_duplicado"] is False, "el que quedó solo ya no es duplicado"


def test_borrar_uno_de_dos_gastos_duplicados_limpia_la_advertencia(client, auth_headers):
    primero = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    segundo = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    assert segundo["es_duplicado"] is True

    client.delete(f"/gastos/{segundo['id']}", headers=auth_headers)

    quedo = client.get(f"/gastos/{primero['id']}", headers=auth_headers)
    assert quedo.json()["es_duplicado"] is False


def test_editar_un_gasto_hasta_igualar_a_otro_lo_marca(client, auth_headers):
    primero = client.post("/gastos/", json=GASTO_BASE, headers=auth_headers).json()
    segundo = client.post("/gastos/", json={**GASTO_BASE, "monto": 1234}, headers=auth_headers).json()
    assert segundo["es_duplicado"] is False

    editado = client.put(f"/gastos/{segundo['id']}", json=GASTO_BASE, headers=auth_headers)
    assert editado.json()["es_duplicado"] is True
    assert client.get(f"/gastos/{primero['id']}", headers=auth_headers).json()["es_duplicado"] is True


# ── Listado mes por mes ─────────────────────────────────────────────────────
# La pantalla muestra un mes a la vez: así la lista nunca choca con el tope de
# 200 filas por consulta, por más meses de uso que acumule el usuario.

def _cargar_en(client, auth_headers, fecha, monto=1000):
    client.post("/gastos/", json={**GASTO_BASE, "monto": monto, "fecha": fecha}, headers=auth_headers)


def test_listar_gastos_de_un_mes(client, auth_headers):
    _cargar_en(client, auth_headers, "2026-08-31T23:00:00", 100)  # último momento de agosto
    _cargar_en(client, auth_headers, "2026-09-01T00:00:00", 200)  # primer momento de septiembre
    _cargar_en(client, auth_headers, "2026-09-30T12:00:00", 300)
    _cargar_en(client, auth_headers, "2026-10-01T00:00:00", 400)

    response = client.get("/gastos/?mes=9&anio=2026", headers=auth_headers)
    assert response.status_code == 200
    assert sorted(g["monto"] for g in response.json()) == [200, 300]


def test_listar_gastos_de_diciembre_no_se_pasa_al_anio_siguiente(client, auth_headers):
    _cargar_en(client, auth_headers, "2026-12-15T10:00:00", 100)
    _cargar_en(client, auth_headers, "2027-01-02T10:00:00", 200)
    response = client.get("/gastos/?mes=12&anio=2026", headers=auth_headers)
    assert [g["monto"] for g in response.json()] == [100]


def test_filtro_de_mes_invalido(client, auth_headers):
    assert client.get("/gastos/?mes=13&anio=2026", headers=auth_headers).status_code == 422
    assert client.get("/gastos/?mes=0&anio=2026", headers=auth_headers).status_code == 422
    # Mes sin año (o al revés) es ambiguo: se rechaza en lugar de adivinar.
    assert client.get("/gastos/?mes=9", headers=auth_headers).status_code == 422
    assert client.get("/gastos/?anio=2026", headers=auth_headers).status_code == 422


def test_meses_con_gastos(client, auth_headers):
    _cargar_en(client, auth_headers, "2026-08-10T10:00:00", 100)
    _cargar_en(client, auth_headers, "2026-09-05T10:00:00", 200)
    _cargar_en(client, auth_headers, "2026-09-20T10:00:00", 300)

    response = client.get("/gastos/meses", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == [
        {"anio": 2026, "mes": 9, "cantidad": 2, "total": 500},
        {"anio": 2026, "mes": 8, "cantidad": 1, "total": 100},
    ]


def test_meses_con_gastos_no_cruza_usuarios(client, auth_headers):
    _cargar_en(client, auth_headers, "2026-09-05T10:00:00")
    client.post("/auth/register", json={"nombre": "Otra", "email": "otra@test.com", "password": "password123"})
    token = client.post("/auth/login", data={"username": "otra@test.com", "password": "password123"}).json()["access_token"]
    response = client.get("/gastos/meses", headers={"Authorization": f"Bearer {token}"})
    assert response.json() == []
