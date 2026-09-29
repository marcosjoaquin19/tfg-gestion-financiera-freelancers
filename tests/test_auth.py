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
    assert response.json()["detail"] == "Email o contraseña incorrectos"


def test_login_email_inexistente(client):
    response = client.post("/auth/login", data={
        "username": "noexiste@test.com",
        "password": "password123"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


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
    """Alterar el contenido del token invalida la firma.

    Se modifica el payload (la parte del medio), que es donde viaja el id de
    usuario: es exactamente lo que intentaría quien quisiera hacerse pasar por
    otro. No se toca la firma, porque en base64url los últimos caracteres
    pueden codificar bits de relleno y un cambio ahí no siempre altera el
    valor decodificado.
    """
    cabecera, payload, firma = auth_headers["Authorization"].split(" ")[1].split(".")
    payload_alterado = ("B" if payload[0] != "B" else "C") + payload[1:]
    token_roto = f"{cabecera}.{payload_alterado}.{firma}"
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


# ---------------------------------------------------------------------------
# Clave de firma de los tokens (HU-17): la API no arranca con una clave insegura
# ---------------------------------------------------------------------------

import pytest

from app.services.auth import CLAVE_DE_EJEMPLO, validar_clave_de_firma


@pytest.mark.parametrize("clave, motivo", [
    (None, "Falta SECRET_KEY"),
    ("", "Falta SECRET_KEY"),
    (CLAVE_DE_EJEMPLO, "valor de ejemplo"),
    ("corta-de-31-caracteres-xxxxxxxx", "demasiado corta"),
])
def test_clave_de_firma_insegura_frena_el_arranque(clave, motivo):
    with pytest.raises(RuntimeError, match=motivo):
        validar_clave_de_firma(clave)


def test_clave_de_firma_valida_se_acepta():
    import secrets
    validar_clave_de_firma(secrets.token_urlsafe(48))   # no lanza
    validar_clave_de_firma("x" * 32)                     # justo en el mínimo


# ── Casos bisagra de la revisión final ───────────────────────────────────────

def _registrar(client, email, password="clave12345", nombre="Caso"):
    return client.post("/auth/register", json={"nombre": nombre, "email": email, "password": password})


def test_el_correo_no_distingue_mayusculas(client):
    assert _registrar(client, "maria@correo.com").status_code == 201
    # Misma cuenta escrita con otras mayúsculas: no se puede registrar dos veces…
    repetido = _registrar(client, "Maria@Correo.com")
    assert repetido.status_code == 400
    # …y el login funciona como lo escriba el usuario (el celular pone la mayúscula).
    for como in ("Maria@Correo.com", "  maria@correo.com "):
        r = client.post("/auth/login", data={"username": como, "password": "clave12345"})
        assert r.status_code == 200, como


def test_el_correo_se_guarda_en_minusculas(client):
    assert _registrar(client, "JUAN@Correo.com").json()["email"] == "juan@correo.com"


def test_contrasena_de_mas_de_72_bytes(client):
    # bcrypt ignora lo que pasa de 72 bytes: se rechaza en lugar de truncar.
    r = _registrar(client, "largo@correo.com", password="A" * 73)
    assert r.status_code == 422
    assert _registrar(client, "justo@correo.com", password="A" * 72).status_code == 201


def test_nombre_solo_con_espacios(client):
    assert _registrar(client, "blanco@correo.com", nombre="   ").status_code == 422


def test_login_con_correo_inexistente_tambien_verifica_la_contrasena(client, monkeypatch):
    # Si bcrypt solo corriera cuando el correo existe, el login respondería
    # mucho más rápido para los correos no registrados y el tiempo delataría
    # qué cuentas existen (HU-02). Tiene que verificar igual, contra el hash
    # de relleno, y responder el mismo mensaje.
    from app.routers import auth as router_auth
    llamadas = []
    original = router_auth.verificar_password
    monkeypatch.setattr(router_auth, "verificar_password",
                        lambda pw, h: llamadas.append(h) or original(pw, h))
    _registrar(client, "existe@correo.com")

    inexistente = client.post("/auth/login", data={"username": "nadie@correo.com", "password": "clave12345"})
    mala = client.post("/auth/login", data={"username": "existe@correo.com", "password": "otraclave99"})

    assert llamadas[0] == router_auth.HASH_DE_RELLENO
    assert len(llamadas) == 2 and llamadas[1].startswith("$2b$12$")
    assert inexistente.status_code == mala.status_code == 401
    assert inexistente.json() == mala.json() == {"detail": "Email o contraseña incorrectos"}
