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


def test_factura_pagada_no_puede_volver_a_pendiente(client, auth_headers):
    """PB-04: PAGADA es un estado terminal.

    PUT y DELETE ya rechazaban tocar una factura cobrada, pero PATCH /estado
    la revertía y borraba la fecha de pago.
    """
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    fid = creada["id"]

    pagada = client.patch(
        f"/facturas/{fid}/estado",
        json={"estado": "pagada", "fecha_pago": "2026-09-20"},
        headers=auth_headers,
    )
    assert pagada.status_code == 200
    assert pagada.json()["estado"] == "pagada"

    for destino in ("pendiente", "vencida"):
        revertir = client.patch(
            f"/facturas/{fid}/estado",
            json={"estado": destino},
            headers=auth_headers,
        )
        assert revertir.status_code == 409, f"se permitió pagada → {destino}"

    # La fecha de pago sigue en su lugar.
    assert client.get(f"/facturas/{fid}", headers=auth_headers).json()["fecha_pago"] is not None


def test_factura_vencida_puede_cobrarse(client, auth_headers):
    """Una factura vencida que finalmente se cobra sí debe poder pasar a pagada."""
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    fid = creada["id"]
    assert client.patch(f"/facturas/{fid}/estado", json={"estado": "vencida"},
                        headers=auth_headers).status_code == 200
    cobrada = client.patch(f"/facturas/{fid}/estado",
                           json={"estado": "pagada", "fecha_pago": "2026-10-05"},
                           headers=auth_headers)
    assert cobrada.status_code == 200
    assert cobrada.json()["estado"] == "pagada"


# ── Validación de datos y reglas de la máquina de estados (revisión M05) ─────
from datetime import datetime, timedelta, timezone


def _en_dias(dias: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).strftime("%Y-%m-%dT00:00:00")


FACTURA_A_FUTURO = {**FACTURA_BASE, "fecha_emision": _en_dias(-5), "fecha_vencimiento": _en_dias(30)}


def test_crear_factura_textos_vacios(client, auth_headers):
    for campo in ("cliente_nombre", "descripcion"):
        response = client.post("/facturas/", json={**FACTURA_BASE, campo: "   "}, headers=auth_headers)
        assert response.status_code == 422, campo


def test_crear_factura_textos_demasiado_largos(client, auth_headers):
    assert client.post("/facturas/", json={**FACTURA_BASE, "cliente_nombre": "x" * 201},
                       headers=auth_headers).status_code == 422
    assert client.post("/facturas/", json={**FACTURA_BASE, "descripcion": "x" * 501},
                       headers=auth_headers).status_code == 422


def test_crear_factura_monto_fuera_de_rango_o_nan(client, auth_headers):
    assert client.post("/facturas/", json={**FACTURA_BASE, "monto": 10 ** 10},
                       headers=auth_headers).status_code == 422
    cuerpo = ('{"cliente_nombre": "Acme", "descripcion": "x", "monto": NaN, '
              '"fecha_emision": "2026-03-01T10:00:00", "fecha_vencimiento": "2026-04-01T10:00:00"}')
    response = client.post("/facturas/", content=cuerpo,
                           headers={**auth_headers, "Content-Type": "application/json"})
    assert response.status_code == 422
    assert client.get("/facturas/", headers=auth_headers).json() == []


def test_no_se_marca_vencida_una_factura_que_no_vencio(client, auth_headers):
    fid = client.post("/facturas/", json=FACTURA_A_FUTURO, headers=auth_headers).json()["id"]
    response = client.patch(f"/facturas/{fid}/estado", json={"estado": "vencida"}, headers=auth_headers)
    assert response.status_code == 409
    assert client.get(f"/facturas/{fid}", headers=auth_headers).json()["estado"] == "pendiente"


def test_fecha_de_pago_anterior_a_la_emision(client, auth_headers):
    fid = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()["id"]
    response = client.patch(f"/facturas/{fid}/estado", json={
        "estado": "pagada", "fecha_pago": "2020-01-01T00:00:00",
    }, headers=auth_headers)
    assert response.status_code == 422


def test_se_puede_cobrar_el_mismo_dia_de_la_emision(client, auth_headers):
    fid = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()["id"]
    mismo_dia = FACTURA_BASE["fecha_emision"][:10] + "T00:00:00"
    response = client.patch(f"/facturas/{fid}/estado", json={
        "estado": "pagada", "fecha_pago": mismo_dia,
    }, headers=auth_headers)
    assert response.status_code == 200


def test_fecha_de_pago_en_una_factura_no_pagada(client, auth_headers):
    fid = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()["id"]
    response = client.patch(f"/facturas/{fid}/estado", json={
        "estado": "vencida", "fecha_pago": "2026-03-20T00:00:00",
    }, headers=auth_headers)
    assert response.status_code == 422


def test_no_se_cambia_la_fecha_de_pago_de_una_factura_pagada(client, auth_headers):
    fid = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()["id"]
    client.patch(f"/facturas/{fid}/estado", json={"estado": "pagada", "fecha_pago": "2026-03-20T00:00:00"},
                 headers=auth_headers)
    response = client.patch(f"/facturas/{fid}/estado", json={
        "estado": "pagada", "fecha_pago": "2026-03-25T00:00:00",
    }, headers=auth_headers)
    assert response.status_code == 409
    assert client.get(f"/facturas/{fid}", headers=auth_headers).json()["fecha_pago"].startswith("2026-03-20")


def test_extender_el_plazo_de_una_vencida_la_vuelve_pendiente(client, auth_headers):
    fid = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()["id"]
    client.patch(f"/facturas/{fid}/estado", json={"estado": "vencida"}, headers=auth_headers)

    response = client.put(f"/facturas/{fid}", json={**FACTURA_BASE, "fecha_vencimiento": _en_dias(30)},
                          headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["estado"] == "pendiente"


def test_acortar_el_plazo_a_una_fecha_pasada_la_vence(client, auth_headers):
    fid = client.post("/facturas/", json=FACTURA_A_FUTURO, headers=auth_headers).json()["id"]
    response = client.put(f"/facturas/{fid}", json={**FACTURA_A_FUTURO, "fecha_vencimiento": _en_dias(-1)},
                          headers=auth_headers)
    assert response.json()["estado"] == "vencida"
