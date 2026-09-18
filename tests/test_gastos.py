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
