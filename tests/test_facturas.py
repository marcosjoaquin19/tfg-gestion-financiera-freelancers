"""
Tests del módulo de Facturas (/facturas).

Verifican el CRUD y las reglas de negocio: vencimiento posterior a la emisión,
cambios de estado (pendiente/pagada/vencida) y que una factura pagada no se
pueda editar ni eliminar.
"""

FACTURA_BASE = {
    "cliente_nombre": "Acme Corp",
    "descripcion": "Desarrollo sitio web",
    "monto": 300000,
    "fecha_emision": "2026-03-01T10:00:00",
    "fecha_vencimiento": "2026-04-01T10:00:00"
}


def test_crear_factura(client, auth_headers):
    response = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["cliente_nombre"] == "Acme Corp"
    assert data["estado"] == "pendiente"
    assert data["fecha_pago"] is None


def test_crear_factura_vencimiento_anterior_a_emision(client, auth_headers):
    response = client.post("/facturas/", json={
        **FACTURA_BASE,
        "fecha_emision": "2026-04-01T10:00:00",
        "fecha_vencimiento": "2026-03-01T10:00:00"
    }, headers=auth_headers)
    assert response.status_code == 422


def test_crear_factura_monto_negativo(client, auth_headers):
    response = client.post("/facturas/", json={**FACTURA_BASE, "monto": -100}, headers=auth_headers)
    assert response.status_code == 422


def test_listar_facturas(client, auth_headers):
    client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers)
    client.post("/facturas/", json={**FACTURA_BASE, "cliente_nombre": "Beta SA"}, headers=auth_headers)
    response = client.get("/facturas/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_listar_facturas_filtro_estado(client, auth_headers):
    client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers)
    response = client.get("/facturas/?estado=pendiente", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_listar_facturas_filtro_cliente(client, auth_headers):
    client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers)
    client.post("/facturas/", json={**FACTURA_BASE, "cliente_nombre": "Beta SA"}, headers=auth_headers)
    # búsqueda parcial case-insensitive
    response = client.get("/facturas/?cliente_nombre=acme", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["cliente_nombre"] == "Acme Corp"


def test_actualizar_estado_a_pagada(client, auth_headers):
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    response = client.patch(f"/facturas/{creada['id']}/estado", json={
        "estado": "pagada",
        "fecha_pago": "2026-03-15T10:00:00"
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "pagada"
    assert data["fecha_pago"] is not None


def test_actualizar_estado_a_pagada_sin_fecha_pago(client, auth_headers):
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    response = client.patch(f"/facturas/{creada['id']}/estado", json={
        "estado": "pagada"
        # sin fecha_pago → debe fallar
    }, headers=auth_headers)
    assert response.status_code == 400


def test_actualizar_estado_a_vencida(client, auth_headers):
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    response = client.patch(f"/facturas/{creada['id']}/estado", json={
        "estado": "vencida"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["estado"] == "vencida"


def test_eliminar_factura(client, auth_headers):
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    assert client.delete(f"/facturas/{creada['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/facturas/{creada['id']}", headers=auth_headers).status_code == 404
