"""
Tests del reporte financiero mensual en PDF (PB-13).

El PDF se genera de verdad con ReportLab: se verifica el código de estado,
el tipo de contenido, el encabezado de descarga y la firma binaria %PDF.
"""

INGRESO = {
    "descripcion": "Proyecto web para cliente",
    "monto": 80000,
    "categoria": "Desarrollo",
    "fecha": "2026-03-05T10:00:00",
}
GASTO = {
    "descripcion": "Hosting mensual",
    "monto": 4000,
    "categoria": "Infraestructura",
    "fecha": "2026-03-06T10:00:00",
}


def test_reporte_pdf_sin_auth(client):
    assert client.get("/reportes/pdf").status_code == 401


def test_descargar_pdf_mes_actual(client, auth_headers):
    # Sin parámetros el endpoint asume el mes corriente y genera el PDF igual,
    # aunque no haya movimientos cargados en el período.
    response = client.get("/reportes/pdf", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert "attachment" in response.headers["content-disposition"]


def test_descargar_pdf_periodo_especifico(client, auth_headers):
    response = client.get("/reportes/pdf?mes=3&anio=2026", headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert "reporte_2026-03.pdf" in response.headers["content-disposition"]


def test_descargar_pdf_con_datos(client, auth_headers):
    # Con ingresos y gastos cargados el reporte debe armarse sin errores.
    client.post("/ingresos/", json=INGRESO, headers=auth_headers)
    client.post("/gastos/", json=GASTO, headers=auth_headers)

    response = client.get("/reportes/pdf?mes=3&anio=2026", headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 1000


def test_descargar_pdf_mes_invalido(client, auth_headers):
    # El mes está acotado a 1-12: un valor fuera de rango lo rechaza la
    # validación de query params antes de generar nada.
    response = client.get("/reportes/pdf?mes=13&anio=2026", headers=auth_headers)
    assert response.status_code == 422
