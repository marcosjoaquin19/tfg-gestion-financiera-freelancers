"""
Tests del módulo de Auditoría (/alertas).

Verifican que la auditoría detecte correctamente las anomalías (gastos
duplicados, montos atípicos, monotributo impago, etc.) y que las alertas se
puedan listar y marcar como resueltas.
"""

from datetime import datetime, timedelta


def _hace(dias: int, hora: str = "10:00:00") -> str:
    """Fecha ISO `dias` días antes de hoy.

    Los detectores de auditoría trabajan sobre una ventana móvil (los últimos
    MESES_VENTANA meses), así que los tests no pueden usar fechas fijas: con el
    paso del calendario quedarían fuera de la ventana y dejarían de detectarse.
    """
    return (datetime.now() - timedelta(days=dias)).strftime(f"%Y-%m-%dT{hora}")


# Par "base" de duplicados: D0 y D0+1 (1 día de diferencia, dentro de la
# ventana de 3 días). Ambos a ~30 días de hoy, bien adentro de la ventana móvil.
D0 = _hace(31)
D1 = _hace(30)
D10 = _hace(21)   # 10 días después de D0: fuera de la ventana de duplicados

GASTO_BASE = {"descripcion": "Gasto test", "monto": 1000, "categoria": "Software", "fecha": D0}
FACTURA_BASE = {
    "cliente_nombre": "Cliente Test",
    "descripcion": "Servicio test",
    "monto": 50000,
    "fecha_emision": _hace(60),
    "fecha_vencimiento": _hace(45),  # ya vencida
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
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D0}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D1}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["detalle"]["gastos_duplicados"] >= 1

    alertas = client.get("/alertas/", headers=auth_headers).json()
    tipos = [a["tipo"] for a in alertas]
    assert "gasto_duplicado" in tipos


def test_no_detecta_duplicado_fuera_de_ventana(client, auth_headers):
    # mismo monto y categoría pero con 10 días de diferencia (fuera de la ventana)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D0}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D10}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["gastos_duplicados"] == 0


def test_detecta_anomalia_estadistica(client, auth_headers):
    # 5 gastos normales de $1000 y uno de $50000 en la misma categoría
    for i in range(5):
        client.post("/gastos/", json={**GASTO_BASE, "monto": 1000, "fecha": _hace(31 - i)}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "monto": 50000, "fecha": _hace(22)}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["anomalias"] >= 1


def test_no_detecta_anomalia_con_pocos_gastos(client, auth_headers):
    # con menos de 5 gastos en la categoría no hay estadística confiable
    client.post("/gastos/", json={**GASTO_BASE, "monto": 50000}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["anomalias"] == 0


def test_detecta_factura_vencida(client, auth_headers):
    # la fecha de vencimiento ya pasó
    client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["discrepancias"] >= 1


def test_detecta_factura_en_estado_vencida(client, auth_headers):
    # el frontend marca automáticamente como VENCIDA la factura pendiente cuyo
    # vencimiento pasó: la auditoría tiene que seguir alertándola igual,
    # porque sigue sin cobrarse
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    client.patch(f"/facturas/{creada['id']}/estado", json={
        "estado": "vencida",
        "fecha_pago": None
    }, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["discrepancias"] >= 1


def test_no_detecta_factura_pagada_como_discrepancia(client, auth_headers):
    creada = client.post("/facturas/", json=FACTURA_BASE, headers=auth_headers).json()
    # la marcamos como pagada antes de auditar
    client.patch(f"/facturas/{creada['id']}/estado", json={
        "estado": "pagada",
        "fecha_pago": _hace(50)
    }, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["discrepancias"] == 0


def test_resolver_alerta(client, auth_headers):
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D0}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D1}, headers=auth_headers)
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
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D0}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D1}, headers=auth_headers)

    # corremos la auditoría dos veces
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)

    alertas = client.get("/alertas/?solo_pendientes=false", headers=auth_headers).json()
    # debe haber exactamente 1 alerta, no 2
    assert len([a for a in alertas if a["tipo"] == "gasto_duplicado"]) == 1


def test_alerta_resuelta_no_reaparece(client, auth_headers):
    # Creamos un duplicado y lo detectamos
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D0}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D1}, headers=auth_headers)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)

    alerta_id = client.get("/alertas/", headers=auth_headers).json()[0]["id"]
    # El usuario la resuelve (acknowledge)
    client.patch(f"/alertas/{alerta_id}/resolver", json={"resuelta": True}, headers=auth_headers)

    # Re-ejecutamos: la condición sigue existiendo, pero NO debe generar una nueva
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    pendientes = client.get("/alertas/?solo_pendientes=true", headers=auth_headers).json()
    assert len([a for a in pendientes if a["tipo"] == "gasto_duplicado"]) == 0


def test_eliminar_gasto_duplicado_resuelve_de_raiz(client, auth_headers):
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D0}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D1}, headers=auth_headers)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)

    alerta_id = client.get("/alertas/", headers=auth_headers).json()[0]["id"]
    # Eliminamos el gasto repetido de raíz desde la alerta
    resp = client.delete(f"/alertas/{alerta_id}/gasto-duplicado", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["resuelta"] is True

    # Quedó un solo gasto y ya no hay duplicados
    gastos = client.get("/gastos/", headers=auth_headers).json()
    assert len(gastos) == 1
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    pendientes = client.get("/alertas/?solo_pendientes=true", headers=auth_headers).json()
    assert len([a for a in pendientes if a["tipo"] == "gasto_duplicado"]) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Detector 5: transferencias entre cuentas propias
#
# Caso real: el usuario transfiere de Galicia a Mercado Pago e importa ambos
# extractos. El débito entra como gasto y el crédito como ingreso; ese
# "ingreso" infla la facturación de 12 meses del monotributo. El detector
# cruza ingresos y gastos ya persistidos (mismo monto, fechas a ≤1 día,
# vocabulario de transferencia) y la alerta permite descartar ambas patas.
# ─────────────────────────────────────────────────────────────────────────────

INGRESO_TRANSF = {
    "descripcion": "Transferencia recibida de Marcos Joaquin",
    "monto": 150000, "categoria": "Otros", "fecha": _hace(20, "14:00:00"),
}
GASTO_TRANSF = {
    "descripcion": "Transf enviada a Mercado Pago",
    "monto": 150000, "categoria": "Otros", "fecha": _hace(20, "13:55:00"),
}


def test_detecta_transferencia_entre_cuentas_propias(client, auth_headers):
    client.post("/ingresos/", json=INGRESO_TRANSF, headers=auth_headers)
    client.post("/gastos/", json=GASTO_TRANSF, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["detalle"]["transferencias_propias"] == 1

    alertas = client.get("/alertas/", headers=auth_headers).json()
    alerta = next(a for a in alertas if a["tipo"] == "transferencia_propia")
    # La alerta referencia AMBAS patas para poder descartarlas sin ambigüedad
    assert alerta["gasto_id_duplicado"] is not None
    assert alerta["ingreso_id_relacionado"] is not None
    assert alerta["monto_involucrado"] == 150000


def test_no_marca_transferencia_sin_vocabulario(client, auth_headers):
    # Mismo monto y mismo día, pero ninguna descripción menciona una
    # transferencia: es una coincidencia legítima (cobro + compra), no un par.
    client.post("/ingresos/", json={**INGRESO_TRANSF, "descripcion": "Honorarios cliente Acme"}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_TRANSF, "descripcion": "Compra notebook"}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["transferencias_propias"] == 0


def test_no_marca_transferencia_con_fechas_lejanas(client, auth_headers):
    # Vocabulario y monto coinciden pero las patas están a 10 días: no es
    # el mismo movimiento.
    client.post("/ingresos/", json={**INGRESO_TRANSF, "fecha": _hace(29)}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_TRANSF, "fecha": _hace(19)}, headers=auth_headers)

    response = client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    assert response.json()["detalle"]["transferencias_propias"] == 0


def test_descartar_transferencia_elimina_ambas_patas(client, auth_headers):
    client.post("/ingresos/", json=INGRESO_TRANSF, headers=auth_headers)
    client.post("/gastos/", json=GASTO_TRANSF, headers=auth_headers)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)

    alertas = client.get("/alertas/", headers=auth_headers).json()
    alerta = next(a for a in alertas if a["tipo"] == "transferencia_propia")

    resp = client.delete(f"/alertas/{alerta['id']}/transferencia-propia", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["resuelta"] is True

    # Ambas patas desaparecieron: el ingreso ya no infla el monotributo
    # y el gasto ya no distorsiona las estadísticas.
    assert client.get("/ingresos/", headers=auth_headers).json() == []
    assert client.get("/gastos/", headers=auth_headers).json() == []

    # Re-ejecutar la auditoría no regenera la alerta (el par ya no existe).
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    pendientes = client.get("/alertas/?solo_pendientes=true", headers=auth_headers).json()
    assert len([a for a in pendientes if a["tipo"] == "transferencia_propia"]) == 0


def test_descartar_transferencia_rechaza_otro_tipo_de_alerta(client, auth_headers):
    # El endpoint de descarte solo aplica a alertas transferencia_propia:
    # con una alerta de gasto duplicado debe responder 400 sin tocar nada.
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D0}, headers=auth_headers)
    client.post("/gastos/", json={**GASTO_BASE, "fecha": D1}, headers=auth_headers)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)

    alerta_id = client.get("/alertas/", headers=auth_headers).json()[0]["id"]
    resp = client.delete(f"/alertas/{alerta_id}/transferencia-propia", headers=auth_headers)
    assert resp.status_code == 400
    assert len(client.get("/gastos/", headers=auth_headers).json()) == 2


def test_eliminar_duplicado_no_confunde_pares_con_mismo_monto(client, auth_headers):
    # Regresión: dos pares de duplicados DISTINTOS que comparten el mismo
    # monto y categoría. Antes el gasto a eliminar se localizaba solo por
    # monto y podía borrarse el del par equivocado; ahora la alerta guarda
    # la referencia directa (gasto_id_duplicado) al gasto repetido.
    par = {"descripcion": "Hosting mensual", "monto": 5000, "categoria": "Infraestructura"}
    # Par "abril": dos gastos a 60 y 59 días; par "mayo": a 30 y 29 días.
    ids_abril = {
        client.post("/gastos/", json={**par, "fecha": _hace(60)}, headers=auth_headers).json()["id"],
        client.post("/gastos/", json={**par, "fecha": _hace(59)}, headers=auth_headers).json()["id"],
    }
    id_sobreviviente_mayo = client.post("/gastos/", json={**par, "fecha": _hace(30)}, headers=auth_headers).json()["id"]
    r_dup_mayo = client.post("/gastos/", json={**par, "fecha": _hace(29)}, headers=auth_headers)
    id_dup_mayo = r_dup_mayo.json()["id"]

    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)
    alertas = client.get("/alertas/", headers=auth_headers).json()
    alerta_mayo = next(
        a for a in alertas
        if a["tipo"] == "gasto_duplicado" and a["gasto_id_duplicado"] == id_dup_mayo
    )

    resp = client.delete(f"/alertas/{alerta_mayo['id']}/gasto-duplicado", headers=auth_headers)
    assert resp.status_code == 200

    gastos = client.get("/gastos/", headers=auth_headers).json()
    ids = {g["id"] for g in gastos}
    assert id_dup_mayo not in ids  # se borró exactamente el repetido de mayo

    # El par de abril quedó intacto y sigue marcado como duplicado.
    abril = [g for g in gastos if g["id"] in ids_abril]
    assert len(abril) == 2
    assert all(g["es_duplicado"] for g in abril)

    # El sobreviviente de mayo ya no integra ningún par → se desmarcó.
    mayo = [g for g in gastos if g["id"] == id_sobreviviente_mayo]
    assert len(mayo) == 1
    assert mayo[0]["es_duplicado"] is False
