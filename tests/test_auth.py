"""
Tests del módulo de Autenticación (/auth).

Verifican el registro y el login: alta exitosa, rechazo de emails duplicados,
validaciones y obtención del token JWT con credenciales correctas/incorrectas.
"""


def test_register_exitoso(client):
    response = client.post("/auth/register", json={
        "nombre": "Marcos",
        "email": "marcos@test.com",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "marcos@test.com"
    assert data["nombre"] == "Marcos"
    assert data["es_activo"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_register_email_duplicado(client):
    payload = {"nombre": "Marcos", "email": "marcos@test.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_register_email_invalido(client):
    response = client.post("/auth/register", json={
        "nombre": "Marcos",
        "email": "no-es-un-email",
        "password": "password123"
    })
    assert response.status_code == 422


def test_login_exitoso(client, usuario_registrado):
    response = client.post("/auth/login", data={
        "username": usuario_registrado["email"],
        "password": usuario_registrado["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_password_incorrecto(client, usuario_registrado):
    response = client.post("/auth/login", data={
        "username": usuario_registrado["email"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    # el mensaje no debe revelar si el email existe o no
    assert response.json()["detail"] == "Email o password incorrectos"


def test_login_email_inexistente(client):
    response = client.post("/auth/login", data={
        "username": "noexiste@test.com",
        "password": "password123"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o password incorrectos"
