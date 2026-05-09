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


# ─────────────────────────────────────────────────────────────────────────────
# Detección de duplicados — los 6 escenarios discutidos con el alumno
#
# La idea no es que el sistema decida solo qué descartar: marca con la flag
# posible_duplicado las filas que ya están en BD para que el frontend
# desactive el checkbox por defecto. Como red de seguridad, /confirmar
# vuelve a aplicar la detección server-side.
# ─────────────────────────────────────────────────────────────────────────────


def _gasto(fecha, desc, monto, categoria="Software"):
    return {
        "fecha": fecha, "descripcion": desc, "monto": monto,
        "tipo": "gasto", "categoria": categoria,
    }


def _ingreso(fecha, desc, monto, categoria="Servicios"):
    return {
        "fecha": fecha, "descripcion": desc, "monto": monto,
        "tipo": "ingreso", "categoria": categoria,
    }


def test_caso_A_cobros_mensuales_recurrentes_no_son_duplicados(client, auth_headers):
    # Escenario A: "Honorarios Acme" $50.000 cada mes. Aunque la descripción
    # y el monto coinciden, las fechas distintas evitan la marca.
    primera = client.post(
        "/importar/confirmar",
        json={"movimientos": [_ingreso("2026-03-15T00:00:00", "Honorarios Acme", 50000)], "mapeo": {}},
        headers=auth_headers,
    )
    assert primera.status_code == 200
    assert primera.json()["importados"] == 1

    segunda = client.post(
        "/importar/confirmar",
        json={"movimientos": [_ingreso("2026-04-15T00:00:00", "Honorarios Acme", 50000)], "mapeo": {}},
        headers=auth_headers,
    )
    assert segunda.status_code == 200
    assert segunda.json()["importados"] == 1
    assert segunda.json()["omitidos_por_duplicado"] == 0


def test_caso_C_dos_cafes_mismo_dia_se_importan_los_dos(client, auth_headers):
    # Escenario C: el usuario fue dos veces a la misma cafetería el mismo día
    # y gastó lo mismo. Ambas filas son legítimas y deben importarse.
    payload = {
        "movimientos": [
            _gasto("2026-03-01T00:00:00", "Cafe Starbucks", 1500, "Alimentación"),
            _gasto("2026-03-01T00:00:00", "Cafe Starbucks", 1500, "Alimentación"),
        ],
        "mapeo": {},
    }
    response = client.post("/importar/confirmar", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["importados"] == 2
    assert data["omitidos_por_duplicado"] == 0


def test_caso_C_prima_reimport_de_dos_cafes_marca_ambos_duplicados(client, auth_headers):
    # Escenario C': después de cargar dos cafés legítimos, si el usuario
    # vuelve a importar el mismo CSV ambos deben marcarse como duplicados.
    movimientos = [
        _gasto("2026-03-01T00:00:00", "Cafe Starbucks", 1500, "Alimentación"),
        _gasto("2026-03-01T00:00:00", "Cafe Starbucks", 1500, "Alimentación"),
    ]
    primera = client.post("/importar/confirmar", json={"movimientos": movimientos, "mapeo": {}}, headers=auth_headers)
    assert primera.json()["importados"] == 2

    # Re-import del mismo CSV
    segunda = client.post("/importar/confirmar", json={"movimientos": movimientos, "mapeo": {}}, headers=auth_headers)
    assert segunda.status_code == 200
    data = segunda.json()
    assert data["importados"] == 0
    assert data["omitidos_por_duplicado"] == 2


def test_caso_C_extension_csv_trae_mas_instancias_que_BD(client, auth_headers):
    # El CSV trae 3 cafés del mismo día pero en BD ya había 2 (de una carga
    # previa). Solo dos deben omitirse, el tercero debe importarse.
    primera = client.post(
        "/importar/confirmar",
        json={
            "movimientos": [
                _gasto("2026-03-01T00:00:00", "Cafe", 1500, "Alimentación"),
                _gasto("2026-03-01T00:00:00", "Cafe", 1500, "Alimentación"),
            ],
            "mapeo": {},
        },
        headers=auth_headers,
    )
    assert primera.json()["importados"] == 2

    segunda = client.post(
        "/importar/confirmar",
        json={
            "movimientos": [
                _gasto("2026-03-01T00:00:00", "Cafe", 1500, "Alimentación"),
                _gasto("2026-03-01T00:00:00", "Cafe", 1500, "Alimentación"),
                _gasto("2026-03-01T00:00:00", "Cafe", 1500, "Alimentación"),
            ],
            "mapeo": {},
        },
        headers=auth_headers,
    )
    assert segunda.status_code == 200
    data = segunda.json()
    assert data["importados"] == 1
    assert data["omitidos_por_duplicado"] == 2


def test_caso_E_re_subir_mismo_csv_omite_todo(client, auth_headers):
    # Escenario E: el usuario sube el mismo archivo dos veces por error.
    # La segunda importación debe omitir todas las filas.
    payload = {
        "movimientos": [
            _gasto("2026-03-05T00:00:00", "Adobe", 3500, "Software"),
            _gasto("2026-03-10T00:00:00", "AWS", 2800, "Infraestructura"),
            _ingreso("2026-03-15T00:00:00", "Cliente Beta", 8000),
        ],
        "mapeo": {},
    }
    primera = client.post("/importar/confirmar", json=payload, headers=auth_headers)
    assert primera.json()["importados"] == 3

    segunda = client.post("/importar/confirmar", json=payload, headers=auth_headers)
    data = segunda.json()
    assert data["importados"] == 0
    assert data["omitidos_por_duplicado"] == 3


def test_caso_D_solapamiento_de_extractos_solo_omite_repetidos(client, auth_headers):
    # Escenario D: el primer extracto cubre del 1 al 15, el segundo cubre
    # del 10 al 20. Las filas del 10 al 15 están en ambos: deben omitirse.
    primera_payload = {
        "movimientos": [
            _gasto("2026-03-05T00:00:00", "Compra A", 1000, "Otros"),
            _gasto("2026-03-10T00:00:00", "Compra B", 2000, "Otros"),
            _gasto("2026-03-15T00:00:00", "Compra C", 3000, "Otros"),
        ],
        "mapeo": {},
    }
    client.post("/importar/confirmar", json=primera_payload, headers=auth_headers)

    segunda_payload = {
        "movimientos": [
            _gasto("2026-03-10T00:00:00", "Compra B", 2000, "Otros"),  # duplicado
            _gasto("2026-03-15T00:00:00", "Compra C", 3000, "Otros"),  # duplicado
            _gasto("2026-03-18T00:00:00", "Compra D", 4000, "Otros"),  # nuevo
            _gasto("2026-03-20T00:00:00", "Compra E", 5000, "Otros"),  # nuevo
        ],
        "mapeo": {},
    }
    response = client.post("/importar/confirmar", json=segunda_payload, headers=auth_headers)
    data = response.json()
    assert data["importados"] == 2
    assert data["omitidos_por_duplicado"] == 2


def test_descripcion_normalizada_iguala_mayusculas_y_tildes(client, auth_headers):
    # Una variación común entre exports: el mismo movimiento aparece como
    # "ADOBE PHOTOSHOP" en un extracto y "Adobe Photoshop" en otro. Tienen
    # que tratarse como el mismo movimiento.
    primera = client.post(
        "/importar/confirmar",
        json={"movimientos": [_gasto("2026-03-01T00:00:00", "ADOBE  PHOTOSHOP", 1200)], "mapeo": {}},
        headers=auth_headers,
    )
    assert primera.json()["importados"] == 1

    segunda = client.post(
        "/importar/confirmar",
        json={"movimientos": [_gasto("2026-03-01T00:00:00", "Adobe Photoshop", 1200)], "mapeo": {}},
        headers=auth_headers,
    )
    data = segunda.json()
    assert data["importados"] == 0
    assert data["omitidos_por_duplicado"] == 1
