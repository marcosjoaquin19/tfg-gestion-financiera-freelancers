from unittest.mock import patch


def test_clasificar_gasto_sin_auth(client):
    response = client.post("/gastos/clasificar", json={"descripcion": "Adobe Photoshop"})
    assert response.status_code == 401


def test_clasificar_gasto_exitoso(client, auth_headers):
    with patch("app.services.ia_service._llamar_groq", return_value="Software"):
        response = client.post(
            "/gastos/clasificar",
            json={"descripcion": "Adobe Photoshop"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "categoria_sugerida" in data
    assert data["categoria_sugerida"] == "Software"


def test_resumen_financiero_sin_auth(client):
    response = client.get("/resumen/financiero")
    assert response.status_code == 401


def test_resumen_financiero_exitoso(client, auth_headers):
    mock_resumen = ("Tus finanzas están en orden este mes.", True)
    with patch("app.routers.resumen.generar_resumen_financiero", return_value=mock_resumen):
        response = client.get("/resumen/financiero?mes=3&anio=2026", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "resumen" in data
    assert "generado_con_ia" in data
    assert "periodo" in data


def test_recomendaciones_sin_auth(client):
    response = client.get("/recomendaciones/")
    assert response.status_code == 401


def test_recomendaciones_exitoso(client, auth_headers):
    mock_result = {
        "recomendaciones": [
            "Revisá tus gastos en Software.",
            "Cobrá las facturas pendientes esta semana.",
        ],
        "generado_con_ia": True,
    }
    with patch("app.routers.recomendaciones.generar_recomendaciones", return_value=mock_result):
        response = client.get("/recomendaciones/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "recomendaciones" in data
    assert isinstance(data["recomendaciones"], list)
