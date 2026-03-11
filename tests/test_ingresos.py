import pytest

INGRESO_BASE = {
    "descripcion": "Proyecto web",
    "monto": 150000,
    "categoria": "Desarrollo",
    "fecha": "2026-03-01T10:00:00"
}


def test_crear_ingreso(client, auth_headers):
    response = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["descripcion"] == INGRESO_BASE["descripcion"]
    assert data["monto"] == INGRESO_BASE["monto"]
    assert data["usuario_id"] == 1


def test_crear_ingreso_sin_auth(client):
    response = client.post("/ingresos/", json=INGRESO_BASE)
    assert response.status_code == 401


def test_crear_ingreso_monto_negativo(client, auth_headers):
    response = client.post("/ingresos/", json={**INGRESO_BASE, "monto": -100}, headers=auth_headers)
    assert response.status_code == 422


def test_crear_ingreso_monto_cero(client, auth_headers):
    response = client.post("/ingresos/", json={**INGRESO_BASE, "monto": 0}, headers=auth_headers)
    assert response.status_code == 422


def test_listar_ingresos(client, auth_headers):
    client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)
    client.post("/ingresos/", json={**INGRESO_BASE, "descripcion": "Otro proyecto"}, headers=auth_headers)
    response = client.get("/ingresos/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_listar_ingresos_filtro_categoria(client, auth_headers):
    client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)
    client.post("/ingresos/", json={**INGRESO_BASE, "categoria": "Diseño"}, headers=auth_headers)
    response = client.get("/ingresos/?categoria=Diseño", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["categoria"] == "Diseño"


def test_obtener_ingreso(client, auth_headers):
    creado = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers).json()
    response = client.get(f"/ingresos/{creado['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == creado["id"]


def test_obtener_ingreso_inexistente(client, auth_headers):
    response = client.get("/ingresos/9999", headers=auth_headers)
    assert response.status_code == 404


def test_actualizar_ingreso(client, auth_headers):
    creado = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers).json()
    response = client.put(f"/ingresos/{creado['id']}", json={**INGRESO_BASE, "monto": 200000}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["monto"] == 200000


def test_eliminar_ingreso(client, auth_headers):
    creado = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers).json()
    response = client.delete(f"/ingresos/{creado['id']}", headers=auth_headers)
    assert response.status_code == 204
    # verificamos que ya no existe
    assert client.get(f"/ingresos/{creado['id']}", headers=auth_headers).status_code == 404


def test_usuario_no_ve_ingresos_de_otro(client):
    # registramos dos usuarios distintos
    client.post("/auth/register", json={"nombre": "User1", "email": "user1@test.com", "password": "pass1"})
    client.post("/auth/register", json={"nombre": "User2", "email": "user2@test.com", "password": "pass2"})

    token1 = client.post("/auth/login", json={"email": "user1@test.com", "password": "pass1"}).json()["access_token"]
    token2 = client.post("/auth/login", json={"email": "user2@test.com", "password": "pass2"}).json()["access_token"]

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # user1 crea un ingreso
    creado = client.post("/ingresos/", json=INGRESO_BASE, headers=headers1).json()

    # user2 intenta acceder al ingreso de user1
    response = client.get(f"/ingresos/{creado['id']}", headers=headers2)
    assert response.status_code == 404
