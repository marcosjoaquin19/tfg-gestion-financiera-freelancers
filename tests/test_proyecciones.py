"""
Tests del módulo de Proyecciones (/proyecciones).

Verifican la generación de proyecciones con Prophet (mockeado), el manejo del
caso con pocos datos históricos y el listado de proyecciones guardadas.
"""

from unittest.mock import patch, MagicMock
import pandas as pd

INGRESO_BASE = {"descripcion": "Ingreso test", "monto": 100000, "categoria": "Desarrollo", "fecha": "2026-01-01T10:00:00"}


def _crear_ingresos(client, headers, cantidad):
    for i in range(cantidad):
        fecha = f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T10:00:00"
        client.post("/ingresos/", json={**INGRESO_BASE, "fecha": fecha, "monto": 100000 + i * 1000}, headers=headers)


def test_generar_proyecciones_sin_suficientes_datos(client, auth_headers):
    # con pocos datos usa Cold Start y devuelve proyecciones igual
    _crear_ingresos(client, auth_headers, 5)
    response = client.post("/proyecciones/generar", json={"periodos": 30}, headers=auth_headers)
    assert response.status_code == 201


def test_generar_proyecciones_exitoso(client, auth_headers):
    _crear_ingresos(client, auth_headers, 12)

    # mockeamos Prophet para no depender del modelo real en los tests
    forecast_mock = pd.DataFrame({
        "ds": pd.date_range("2026-06-01", periods=30),
        "yhat": [120000.0] * 30,
        "yhat_lower": [100000.0] * 30,
        "yhat_upper": [140000.0] * 30,
    })

    with patch("app.services.prophet_service.Prophet") as MockProphet:
        instancia = MagicMock()
        instancia.predict.return_value = forecast_mock
        instancia.make_future_dataframe.return_value = forecast_mock
        MockProphet.return_value = instancia

        response = client.post("/proyecciones/generar", json={"periodos": 30}, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 30
    assert data[0]["monto_proyectado"] >= 0
    assert data[0]["monto_lower"] >= 0
    assert data[0]["monto_upper"] >= 0


def test_generar_proyecciones_reemplaza_anteriores(client, auth_headers):
    _crear_ingresos(client, auth_headers, 12)

    forecast_mock = pd.DataFrame({
        "ds": pd.date_range("2026-06-01", periods=10),
        "yhat": [120000.0] * 10,
        "yhat_lower": [100000.0] * 10,
        "yhat_upper": [140000.0] * 10,
    })

    with patch("app.services.prophet_service.Prophet") as MockProphet:
        instancia = MagicMock()
        instancia.predict.return_value = forecast_mock
        instancia.make_future_dataframe.return_value = forecast_mock
        MockProphet.return_value = instancia

        client.post("/proyecciones/generar", json={"periodos": 10}, headers=auth_headers)
        client.post("/proyecciones/generar", json={"periodos": 10}, headers=auth_headers)

    # después de dos generaciones solo debe haber 10 proyecciones, no 20
    response = client.get("/proyecciones/", headers=auth_headers)
    assert len(response.json()) == 10


def test_listar_proyecciones_vacio(client, auth_headers):
    response = client.get("/proyecciones/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_proyecciones_sin_auth(client):
    response = client.get("/proyecciones/")
    assert response.status_code == 401


def test_generar_proyecciones_historial_en_un_solo_mes(client, auth_headers):
    # Regresión: con 10+ ingresos concentrados en un único mes, el DataFrame
    # mensual queda con una sola fila y el fit de Prophet falla (500). El
    # servicio debe detectarlo y caer a la estrategia de media móvil.
    for i in range(12):
        client.post(
            "/ingresos/",
            json={**INGRESO_BASE, "fecha": f"2026-01-{i + 1:02d}T10:00:00", "monto": 90000 + i * 500},
            headers=auth_headers,
        )

    response = client.post("/proyecciones/generar", json={"periodos": 6}, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 6
    assert all(p["monto_proyectado"] > 0 for p in data)
