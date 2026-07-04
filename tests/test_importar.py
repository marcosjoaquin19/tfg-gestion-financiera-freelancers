"""
Tests del módulo de Importación (/importar).

Verifican la detección de columnas del extracto, la clasificación de movimientos
en ingresos/gastos, la detección de duplicados y el guardado final.
"""

import io
from unittest.mock import patch

import pandas as pd


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


def test_importar_preview_extension_no_soportada(client, auth_headers):
    # Subir .txt: el endpoint debe rechazarlo antes incluso de leer el contenido.
    response = client.post(
        "/importar/preview",
        files={"archivo": ("test.txt", io.BytesIO(b"cualquier cosa"), "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Formato no soportado" in response.json()["detail"]


def test_importar_preview_xlsx_valido(client, auth_headers):
    # Generamos un .xlsx en memoria con pandas + openpyxl. Esto recorre
    # todo el camino real del endpoint: leer_dataframe → detectar columnas →
    # procesar filas → detectar duplicados → clasificar preview.
    df = pd.DataFrame([
        {"fecha": "2026-01-01", "descripcion": "Adobe Photoshop", "monto": -1200},
        {"fecha": "2026-01-02", "descripcion": "Pago cliente Acme", "monto": 5000},
    ])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    response = client.post(
        "/importar/preview",
        files={
            "archivo": (
                "extracto.xlsx",
                buffer,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_filas"] == 2
    # El detector reconoce las columnas aunque vengan de Excel.
    assert data["mapeo_detectado"]["columna_fecha"] == "fecha"
    assert data["mapeo_detectado"]["columna_descripcion"] == "descripcion"
    # Una fila negativa (gasto) y una positiva (ingreso).
    tipos = {fila["tipo"] for fila in data["preview"]}
    assert tipos == {"gasto", "ingreso"}


def test_importar_preview_csv_con_preambulo_de_metadata(client, auth_headers):
    # Los exports reales de Galicia, Santander Río, BBVA, Macro y Nación
    # anteponen filas de metadata (titular, CBU, período) antes de la tabla.
    # leer_dataframe debe detectar la fila-encabezado real y descartar lo de
    # arriba. Además este archivo usa columnas Débito/Crédito y números en
    # formato argentino (92.300,50) para cubrir todo el camino de una vez.
    csv = (
        "Banco Galicia - Consulta de Movimientos\n"
        "Cuenta: Caja de Ahorro en Pesos 4000123-4\n"
        "Titular: PEREZ JUAN - CUIT 20-30123456-7\n"
        "Período: 01/04/2026 al 30/04/2026\n"
        "\n"
        "Fecha;Descripción;Origen;Débito;Crédito;Saldo\n"
        "03/04/2026;ACREDITACION HABERES;Transferencia;;485.000,00;485.000,00\n"
        "07/04/2026;PAGO TARJETA VISA;Débito automático;92.300,50;;392.699,50\n"
    )
    response = client.post(
        "/importar/preview",
        files={"archivo": ("galicia.csv", io.BytesIO(csv.encode("utf-8")), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_filas"] == 2

    mapeo = data["mapeo_detectado"]
    assert mapeo["columna_fecha"] == "Fecha"
    assert mapeo["columna_debito"] == "Débito"
    assert mapeo["columna_credito"] == "Crédito"

    movimientos = {m["descripcion"]: m for m in data["preview"]}
    # Crédito → ingreso, Débito → gasto, con el número argentino bien parseado.
    assert movimientos["ACREDITACION HABERES"]["tipo"] == "ingreso"
    assert movimientos["ACREDITACION HABERES"]["monto"] == 485000.0
    assert movimientos["PAGO TARJETA VISA"]["tipo"] == "gasto"
    assert movimientos["PAGO TARJETA VISA"]["monto"] == 92300.5


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


def test_importar_preview_clasifica_lote_completo(client, auth_headers):
    # Regresión: /confirmar persiste exactamente lo que devuelve /preview,
    # así que el preview debe clasificar TODAS las filas del archivo, no solo
    # las 20 que el frontend muestra como muestra visual. Con un archivo de
    # 25 filas, importar tiene que crear 25 registros (antes se perdían 5).
    filas = "\n".join(
        f"2026-03-{(i % 28) + 1:02d},Movimiento bancario numero {i},-{100 + i}"
        for i in range(25)
    )
    csv_bytes = f"fecha,descripcion,monto\n{filas}\n".encode()

    response = client.post(
        "/importar/preview",
        files={"archivo": ("extracto.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_filas"] == 25
    assert len(data["preview"]) == 25
    # todas las filas vuelven con una categoría asignada por el ML local
    assert all(m.get("categoria") for m in data["preview"])

    confirmar = client.post(
        "/importar/confirmar",
        json={"movimientos": data["preview"], "mapeo": data["mapeo_detectado"]},
        headers=auth_headers,
    )
    assert confirmar.status_code == 200
    assert confirmar.json()["importados"] == 25


def test_importar_preview_respeta_correcciones_usuario(client, auth_headers):
    # La clasificación en lote debe respetar la misma prioridad que la
    # individual: si el usuario ya corrigió esa descripción en el playground,
    # la corrección (ground truth) manda sobre la predicción del modelo.
    client.post(
        "/ml/corregir",
        json={"descripcion": "debito servicio xyzeta", "categoria_correcta": "Marketing"},
        headers=auth_headers,
    )

    csv_bytes = b"fecha,descripcion,monto\n2026-03-01,debito servicio xyzeta,-500\n"
    response = client.post(
        "/importar/preview",
        files={"archivo": ("extracto.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["preview"][0]["categoria"] == "Marketing"
