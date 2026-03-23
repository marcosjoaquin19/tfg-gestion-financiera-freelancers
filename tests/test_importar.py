import io
from unittest.mock import patch


def test_importar_preview_sin_auth(client):
    csv_bytes = b"fecha,descripcion,monto\n2026-01-01,Adobe Photoshop,1200\n"
    response = client.post(
        "/importar/preview",
        files={"archivo": ("test.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert response.status_code == 401


def test_importar_preview_csv_valido(client, auth_headers):
    csv_bytes = b"fecha,descripcion,monto\n2026-01-01,Adobe Photoshop,1200\n2026-01-02,Netflix,500\n"

    mock_mapeo = {
        "columna_fecha": "fecha",
        "columna_descripcion": "descripcion",
        "columna_monto": "monto",
        "columna_debito": None,
        "columna_credito": None,
        "columna_tipo": None,
        "formato_fecha": "YYYY-MM-DD",
    }
    mock_movimientos = [
        {"fecha": "2026-01-01", "descripcion": "Adobe Photoshop", "monto": 1200.0, "tipo": "gasto"},
        {"fecha": "2026-01-02", "descripcion": "Netflix", "monto": 500.0, "tipo": "gasto"},
    ]
    mock_preview = [
        {"fecha": "2026-01-01", "descripcion": "Adobe Photoshop", "monto": 1200.0, "tipo": "gasto", "categoria": "Software"},
        {"fecha": "2026-01-02", "descripcion": "Netflix", "monto": 500.0, "tipo": "gasto", "categoria": "Suscripciones"},
    ]

    with patch("app.routers.importar.detectar_columnas_csv", return_value=mock_mapeo), \
         patch("app.routers.importar.procesar_csv", return_value=mock_movimientos), \
         patch("app.routers.importar.clasificar_movimientos", return_value=mock_preview):
        response = client.post(
            "/importar/preview",
            files={"archivo": ("test.csv", io.BytesIO(csv_bytes), "text/csv")},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "total_filas" in data
    assert "preview" in data
    assert data["total_filas"] == 2


def test_importar_confirmar_sin_auth(client):
    response = client.post("/importar/confirmar", json={"movimientos": [], "mapeo": {}})
    assert response.status_code == 401


def test_importar_confirmar_exitoso(client, auth_headers):
    payload = {
        "movimientos": [
            {
                "fecha": "2026-01-01T00:00:00",
                "descripcion": "Adobe Photoshop",
                "monto": 1200.0,
                "tipo": "gasto",
                "categoria": "Software",
            },
            {
                "fecha": "2026-01-02T00:00:00",
                "descripcion": "Pago cliente",
                "monto": 5000.0,
                "tipo": "ingreso",
                "categoria": "Servicios",
            },
        ],
        "mapeo": {},
    }
    response = client.post("/importar/confirmar", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["importados"] > 0
