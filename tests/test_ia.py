"""
Tests del módulo de IA (/resumen y /recomendaciones).

Verifican el resumen financiero (con la llamada a Groq mockeada) y las
recomendaciones determinísticas, incluido el caso sin datos suficientes.
"""

from unittest.mock import patch


def test_clasificar_gasto_sin_auth(client):
    response = client.post("/gastos/clasificar", json={"descripcion": "Adobe Photoshop"})
    assert response.status_code == 401


def test_clasificar_gasto_exitoso(client, auth_headers):
    # Política de soberanía de datos: la clasificación se hace solo con el ML
    # local. Mockeamos ml_service.clasificar_gasto para simular alta confianza.
    mock_ml = {
        "categoria": "Software",
        "confianza": 0.92,
        "fuente": "ml_propio",
        "algoritmo": "naive_bayes",
    }
    with patch("app.services.ml_service.clasificar_gasto", return_value=mock_ml):
        response = client.post(
            "/gastos/clasificar",
            json={"descripcion": "Adobe Photoshop"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "categoria_sugerida" in data
    assert data["categoria_sugerida"] == "Software"
    assert data["fuente"] == "ml_propio"
    assert data["requiere_revision"] is False


def test_clasificar_usa_correccion_previa_del_usuario(client, auth_headers):
    # Si el usuario ya corrigió explícitamente esa descripción, /gastos/clasificar
    # devuelve la corrección sin pasar por el ML: confianza 1.0, fuente
    # 'correccion_usuario', requiere_revision False. Es ground truth.
    client.post(
        "/ml/corregir",
        json={"descripcion": "frase única que el usuario corrige", "categoria_correcta": "Capacitación"},
        headers=auth_headers,
    )
    # La búsqueda es tolerante a variaciones tipográficas: mayúsculas,
    # tildes y espacios múltiples no rompen el match.
    for variante in [
        "frase única que el usuario corrige",
        "Frase Única Que El Usuario Corrige",
        "FRASE UNICA QUE EL USUARIO CORRIGE",
        "  frase  única   que el usuario corrige  ",
    ]:
        response = client.post(
            "/gastos/clasificar",
            json={"descripcion": variante},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["categoria_sugerida"] == "Capacitación", f"falló con {variante!r}"
        assert data["fuente"] == "correccion_usuario"
        assert data["confianza"] == 1.0
        assert data["requiere_revision"] is False


def test_clasificar_gasto_baja_confianza_marca_revision(client, auth_headers):
    # Si el ML local devuelve confianza por debajo del umbral, se sugiere
    # "Otros" y se marca para revisión manual. NUNCA se llama a un servicio
    # externo. Usamos 0.15 para garantizar que quede bajo cualquier umbral
    # razonable que pueda ajustarse en el futuro.
    mock_ml = {
        "categoria": "Software",
        "confianza": 0.15,
        "fuente": "ml_propio",
        "algoritmo": "naive_bayes",
    }
    with patch("app.services.ml_service.clasificar_gasto", return_value=mock_ml):
        response = client.post(
            "/gastos/clasificar",
            json={"descripcion": "ZZZ texto desconocido"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["categoria_sugerida"] == "Otros"
    assert data["requiere_revision"] is True


def test_resumen_financiero_sin_auth(client):
    response = client.get("/resumen/financiero")
    assert response.status_code == 401


def test_resumen_financiero_exitoso(client, auth_headers):
    mock_resumen = ("Tus finanzas están en orden este mes.", True, False)
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
