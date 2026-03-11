from datetime import datetime, timedelta

GASTO_BASE = {"descripcion": "Gasto test", "monto": 1000, "categoria": "Software", "fecha": "2026-03-01T10:00:00"}
FACTURA_BASE = {
    "cliente_nombre": "Cliente Test",
    "descripcion": "Servicio test",
    "monto": 50000,
    "fecha_emision": "2026-01-01T10:00:00",
    "fecha_vencimiento": "2026-01-15T10:00:00",  # ya vencida
}


def test_auditoria_sin_datos(client, auth_headers):
    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["detalle"]["gastos_duplicados"] == 0
    assert data["detalle"]["anomalias"] == 0
    assert data["detalle"]["discrepancias"] == 0


def test_detecta_gasto_duplicado(client, auth_headers):
    # mismo monto y categoría con 1 día de diferencia (dentro de la ventana de 3 días)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-01T10:00:00"}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-02T10:00:00"}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["detalle"]["gastos_duplicados"] >= 1

    alertas = client.get("/alertas/", headers=auth_headers).json()
    tipos = [a["tipo"] for a in alertas]
    assert "gasto_duplicado" in tipos


def test_no_detecta_duplicado_fuera_de_ventana(client, auth_headers):
    # mismo monto y categoría pero con 10 días de diferencia (fuera de la ventana)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-01T10:00:00"}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-11T10:00:00"}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["gastos_duplicados"] == 0


def test_detecta_anomalia_estadistica(client, auth_headers):
    # 5 gastos normales de $1000 y uno de $50000 en la misma categoría
    for i in range(5):
        client.post("/gastos/", json={**GASTO_BASE, "monto": 1000, "fecha": f"2026-03-0{i+1}T10:00:00"}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "monto": 50000, "fecha": "2026-03-10T10:00:00"}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["anomalias"] >= 1


def test_no_detecta_anomalia_con_pocos_gastos(client, auth_headers):
    # con menos de 5 gastos en la categoría no hay estadística confiable
    client.post("/gastos/", json={**GASTO_BASE, "monto": 50000}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["anomalias"] == 0


def test_detecta_factura_vencida(client, auth_headers):
    # la fecha de vencimiento es en enero 2026, ya pasó
    client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["discrepancias"] >= 1


def test_no_detecta_factura_pagada_como_discrepancia(client, auth_headers):
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    # la marcamos como pagada antes de auditar
    client.patch(f"/facturas/{creada['id']}/estado", json={
        "estado": "pagada",
        "fecha_pago": "2026-01-10T10:00:00"
    }, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["discrepancias"] == 0


def test_resolver_alerta(client, auth_headers):
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-01T10:00:00"}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-02T10:00:00"}, headers=auth_headers)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)

    alertas = client.get("/alertas/", headers=auth_headers).json()
    alerta_id = alertas[0]["id"]

    response = client.patch(f"/alertas/{alerta_id}/resolver", json={"resuelta": True}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["resuelta"] is True

    # las alertas resueltas no aparecen en el listado por defecto
    pendientes = client.get("/alertas/", headers=auth_headers).json()
    assert all(a["id"] != alerta_id for a in pendientes)


def test_auditoria_no_duplica_alertas(client, auth_headers):
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-01T10:00:00"}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": "2026-03-02T10:00:00"}, headers=auth_headers)

    # corremos la auditoría dos veces
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)

    alertas = client.get("/alertas/?solo_pendientes=false", headers=auth_headers).json()
    # debe haber exactamente 1 alerta, no 2
    assert len([a for a in alertas if a["tipo"] == "gasto_duplicado"]) == 1
