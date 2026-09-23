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


def test_register_nombre_demasiado_largo(client):
    # La columna `nombre` admite 100 caracteres. Sin un tope en el schema, un
    # nombre más largo llegaba hasta el INSERT y la base devolvía un error 500.
    # Ahora se rechaza antes, con un 422 que explica el problema.
    response = client.post("/auth/register", json={
        "nombre": "A" * 150,
        "email": "nombrelargo@test.com",
        "password": "password123"
    })
    assert response.status_code == 422


def test_register_nombre_vacio(client):
    response = client.post("/auth/register", json={
        "nombre": "",
        "email": "vacio@test.com",
        "password": "password123"
    })
    assert response.status_code == 422


def test_ruta_privada_sin_token(client):
    response = client.get("/ingresos/")
    assert response.status_code == 401


def test_ruta_privada_con_token_manipulado(client, auth_headers):
    # Se altera el último carácter del token: la firma deja de validar.
    token = auth_headers["Authorization"].split(" ")[1]
    token_roto = token[:-1] + ("a" if token[-1] != "a" else "b")
    response = client.get("/ingresos/", headers={"Authorization": f"Bearer {token_roto}"})
    assert response.status_code == 401


def test_aislamiento_entre_usuarios(client, auth_headers):
    """Un usuario no puede leer un recurso creado por otro.

    Es el caso que respalda el "aislamiento por usuario autenticado" del
    Objetivo General: el propietario sale del token, nunca del pedido.
    """
    # Usuario A (auth_headers) crea un ingreso propio.
    creado = client.post("/ingresos/", json={
        "monto": 100000,
        "descripcion": "Proyecto de usuario A",
        "categoria": "Servicios",
        "fecha": "2026-03-01T10:00:00",
    }, headers=auth_headers)
    assert creado.status_code == 201
    ingreso_id = creado.json()["id"]

    # Usuario B se registra e inicia sesión.
    client.post("/auth/register", json={
        "nombre": "Usuario B",
        "email": "usuario.b@test.com",
        "password": "password123",
    })
    login_b = client.post("/auth/login", data={
        "username": "usuario.b@test.com",
        "password": "password123",
    })
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # B pide el ingreso de A por su id: el sistema se comporta como si no existiera.
    ajeno = client.get(f"/ingresos/{ingreso_id}", headers=headers_b)
    assert ajeno.status_code == 404

    # Y el listado de B no incluye nada de A.
    listado_b = client.get("/ingresos/", headers=headers_b)
    assert listado_b.status_code == 200
    assert listado_b.json() == []
