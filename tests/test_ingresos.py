"""
Tests del módulo de Ingresos (/ingresos).

Verifican el alta, listado, edición y borrado de ingresos, las validaciones
(ej: monto positivo) y que cada usuario solo acceda a sus propios ingresos.
"""

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
    client.post("/auth/register", json={"nombre": "User1", "email": "user1@test.com", "password": "password123"})
    client.post("/auth/register", json={"nombre": "User2", "email": "user2@test.com", "password": "password123"})

    token1 = client.post("/auth/login", data={"username": "user1@test.com", "password": "password123"}).json()["access_token"]
    token2 = client.post("/auth/login", data={"username": "user2@test.com", "password": "password123"}).json()["access_token"]

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # user1 crea un ingreso
    creado = client.post("/ingresos/", json=INGRESO_BASE, headers=headers1).json()

    # user2 intenta acceder al ingreso de user1
    response = client.get(f"/ingresos/{creado['id']}", headers=headers2)
    assert response.status_code == 404


def test_crear_ingreso_descripcion_demasiado_larga(client, auth_headers):
    # La columna admite 255 caracteres: un texto más largo llegaba al INSERT
    # y la base devolvía un error 500 sin explicación.
    response = client.post("/ingresos/", json={
        **INGRESO_BASE, "descripcion": "X" * 300,
    }, headers=auth_headers)
    assert response.status_code == 422


def test_crear_ingreso_categoria_demasiado_larga(client, auth_headers):
    response = client.post("/ingresos/", json={
        **INGRESO_BASE, "categoria": "Y" * 200,
    }, headers=auth_headers)
    assert response.status_code == 422


def test_crear_ingreso_descripcion_vacia(client, auth_headers):
    response = client.post("/ingresos/", json={
        **INGRESO_BASE, "descripcion": "",
    }, headers=auth_headers)
    assert response.status_code == 422


def test_crear_ingreso_monto_fuera_de_rango(client, auth_headers):
    # Numeric(12, 2) admite hasta 10 dígitos enteros.
    response = client.post("/ingresos/", json={
        **INGRESO_BASE, "monto": 99999999999999,
    }, headers=auth_headers)
    assert response.status_code == 422


def test_crear_ingreso_monto_maximo_admitido(client, auth_headers):
    # El borde superior válido sí debe entrar.
    response = client.post("/ingresos/", json={
        **INGRESO_BASE, "monto": 9999999999.99,
    }, headers=auth_headers)
    assert response.status_code == 201


# ── Categoría: lista cerrada ────────────────────────────────────────────────

def test_crear_ingreso_categoria_invalida(client, auth_headers):
    response = client.post("/ingresos/", json={
        **INGRESO_BASE, "categoria": "asdasdasd",
    }, headers=auth_headers)
    assert response.status_code == 422
    # El mensaje enumera las categorías válidas para que el cliente pueda corregir.
    assert "Desarrollo" in str(response.json()["detail"])


def test_crear_ingreso_categoria_valida_no_listada_en_gastos(client, auth_headers):
    # "Redacción y Contenido" es propia de ingresos: no está entre las de gasto.
    response = client.post("/ingresos/", json={
        **INGRESO_BASE, "categoria": "Redacción y Contenido",
    }, headers=auth_headers)
    assert response.status_code == 201


# ── Duplicados ──────────────────────────────────────────────────────────────

def test_ingreso_repetido_el_mismo_dia_se_marca(client, auth_headers):
    primero = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)
    assert primero.json()["es_duplicado"] is False

    segundo = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)
    assert segundo.status_code == 201, "la carga repetida se advierte, no se bloquea"
    assert segundo.json()["es_duplicado"] is True

    # El primero también queda marcado: el par se señala completo.
    revisado = client.get(f"/ingresos/{primero.json()['id']}", headers=auth_headers)
    assert revisado.json()["es_duplicado"] is True


def test_plan_de_pagos_en_cuotas_iguales_no_es_duplicado(client, auth_headers):
    """Mismo importe y misma descripción en fechas distintas: son cuotas."""
    cuotas = ["2026-03-10T00:00:00", "2026-04-10T00:00:00", "2026-05-10T00:00:00"]
    for fecha in cuotas:
        respuesta = client.post("/ingresos/", json={
            "descripcion": "Plan de pago cliente Acme - cuota",
            "monto": 250000,
            "categoria": "Consultoría",
            "fecha": fecha,
        }, headers=auth_headers)
        assert respuesta.status_code == 201
        assert respuesta.json()["es_duplicado"] is False, f"la cuota del {fecha} no es duplicado"


def test_cuotas_consecutivas_con_pocos_dias_de_diferencia_no_son_duplicado(client, auth_headers):
    # La regla de gastos usa una ventana de ±3 días; la de ingresos exige el
    # mismo día justamente para no marcar pagos cercanos pero distintos.
    base = {"descripcion": "Honorarios quincena", "monto": 90000, "categoria": "Servicios"}
    a = client.post("/ingresos/", json={**base, "fecha": "2026-03-10T00:00:00"}, headers=auth_headers)
    b = client.post("/ingresos/", json={**base, "fecha": "2026-03-12T00:00:00"}, headers=auth_headers)
    assert a.json()["es_duplicado"] is False
    assert b.json()["es_duplicado"] is False


def test_mismo_monto_y_dia_con_otra_descripcion_no_es_duplicado(client, auth_headers):
    # Dos clientes que pagan lo mismo el mismo día son dos cobros distintos.
    a = client.post("/ingresos/", json={
        **INGRESO_BASE, "descripcion": "Cliente A - landing",
    }, headers=auth_headers)
    b = client.post("/ingresos/", json={
        **INGRESO_BASE, "descripcion": "Cliente B - landing",
    }, headers=auth_headers)
    assert a.json()["es_duplicado"] is False
    assert b.json()["es_duplicado"] is False


def test_duplicado_ignora_mayusculas_y_espacios_sobrantes(client, auth_headers):
    a = client.post("/ingresos/", json={**INGRESO_BASE, "descripcion": "Proyecto Web"}, headers=auth_headers)
    b = client.post("/ingresos/", json={**INGRESO_BASE, "descripcion": "  proyecto   web  "}, headers=auth_headers)
    assert a.json()["es_duplicado"] is False
    assert b.json()["es_duplicado"] is True


def test_corregir_el_monto_retira_la_advertencia_a_los_dos(client, auth_headers):
    primero = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers).json()
    segundo = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers).json()
    assert segundo["es_duplicado"] is True

    # El usuario corrige el importe del segundo: dejan de ser el mismo cobro.
    corregido = client.put(f"/ingresos/{segundo['id']}", json={
        **INGRESO_BASE, "monto": 999000,
    }, headers=auth_headers)
    assert corregido.json()["es_duplicado"] is False

    quedo = client.get(f"/ingresos/{primero['id']}", headers=auth_headers)
    assert quedo.json()["es_duplicado"] is False, "el que quedó solo ya no es duplicado"


def test_borrar_una_de_las_dos_cargas_limpia_la_advertencia(client, auth_headers):
    primero = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers).json()
    segundo = client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers).json()
    assert segundo["es_duplicado"] is True

    client.delete(f"/ingresos/{segundo['id']}", headers=auth_headers)

    quedo = client.get(f"/ingresos/{primero['id']}", headers=auth_headers)
    assert quedo.json()["es_duplicado"] is False


def test_el_duplicado_no_cruza_usuarios(client, auth_headers):
    client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)

    client.post("/auth/register", json={
        "nombre": "Otro", "email": "otro.ingresos@test.com", "password": "password123",
    })
    login = client.post("/auth/login", data={
        "username": "otro.ingresos@test.com", "password": "password123",
    })
    headers_otro = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # El mismo ingreso, pero de otro usuario: no hay relación entre ambos.
    ajeno = client.post("/ingresos/", json=INGRESO_BASE, headers=headers_otro)
    assert ajeno.json()["es_duplicado"] is False


def test_filtro_solo_duplicados(client, auth_headers):
    client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)
    client.post("/ingresos/", json=INGRESO_BASE, headers=auth_headers)
    client.post("/ingresos/", json={
        **INGRESO_BASE, "descripcion": "Otro cobro", "monto": 1234,
    }, headers=auth_headers)

    todos = client.get("/ingresos/", headers=auth_headers)
    assert len(todos.json()) == 3

    duplicados = client.get("/ingresos/?solo_duplicados=true", headers=auth_headers)
    assert len(duplicados.json()) == 2


def test_crear_ingreso_monto_nan_no_se_guarda(client, auth_headers):
    # Antes el NaN pasaba la validación, se guardaba en la base y recién
    # fallaba al armar la respuesta: error 500 con el registro ya persistido.
    cuerpo = ('{"descripcion": "prueba", "monto": NaN, "categoria": "Otros", '
              '"fecha": "2026-03-01T10:00:00"}')
    response = client.post(
        "/ingresos/", content=cuerpo,
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert client.get("/ingresos/", headers=auth_headers).json() == []
