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


# ─────────────────────────────────────────────────────────────────────────────
# Transferencias entre cuentas propias dentro del MISMO lote
#
# Si el archivo trae las dos patas de una transferencia entre cuentas del
# usuario (débito como gasto + crédito como ingreso, mismo monto, fechas a
# ≤1 día, vocabulario de transferencia), /confirmar las omite: ese "ingreso"
# no es facturación real e inflaría el cálculo del monotributo. Las patas
# repartidas entre archivos distintos las cubre la auditoría (detector 5).
# ─────────────────────────────────────────────────────────────────────────────


def test_transferencia_propia_en_mismo_lote_se_omite(client, auth_headers):
    payload = {
        "movimientos": [
            _gasto("2026-06-10T00:00:00", "Transferencia enviada a Mercado Pago", 80000, "Otros"),
            _ingreso("2026-06-10T00:00:00", "Transferencia recibida CVU propio", 80000, "Otros"),
            _ingreso("2026-06-12T00:00:00", "Honorarios cliente Acme", 95000),
        ],
        "mapeo": {},
    }
    response = client.post("/importar/confirmar", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Solo entra el honorario real; las dos patas de la transferencia se omiten.
    assert data["importados"] == 1
    assert data["omitidos_por_transferencia"] == 2
    assert data["ingresos_creados"] == 1
    assert data["gastos_creados"] == 0

    ingresos = client.get("/ingresos/", headers=auth_headers).json()
    assert [i["descripcion"] for i in ingresos] == ["Honorarios cliente Acme"]


def test_coincidencia_de_monto_sin_vocabulario_no_se_omite(client, auth_headers):
    # Guardia contra falsos positivos: un cobro y una compra que casualmente
    # coinciden en monto y fecha NO son una transferencia y deben importarse.
    payload = {
        "movimientos": [
            _gasto("2026-06-10T00:00:00", "Compra notebook Lenovo", 80000, "Hardware"),
            _ingreso("2026-06-10T00:00:00", "Honorarios cliente Beta", 80000),
        ],
        "mapeo": {},
    }
    response = client.post("/importar/confirmar", json=payload, headers=auth_headers)
    data = response.json()
    assert data["importados"] == 2
    assert data["omitidos_por_transferencia"] == 0


def test_preview_resumen_cuenta_transferencias_propias(client, auth_headers):
    # Camino completo del preview con un CSV real: el resumen informa las
    # transferencias detectadas y las descuenta de los "nuevos".
    csv = (
        "fecha,descripcion,monto\n"
        "2026-06-10,Transf a cuenta propia Mercado Pago,-80000\n"
        "2026-06-10,Transferencia recibida Galicia,80000\n"
        "2026-06-12,Pago cliente Acme,95000\n"
    )
    response = client.post(
        "/importar/preview",
        files={"archivo": ("extracto.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resumen"]["transferencias_propias"] == 2
    assert data["resumen"]["nuevos"] == 1
    # Las filas del par vuelven marcadas para que el frontend las muestre
    # atenuadas con la etiqueta "se omite".
    marcadas = [m for m in data["preview"] if m.get("posible_transferencia_propia")]
    assert len(marcadas) == 2


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


# ─────────────────────────────────────────────────────────────────────────────
# HU-07 · último criterio de aceptación:
# "Dada una importación confirmada, cuando falla el procesamiento de algún
#  registro, entonces el sistema revierte todos los anteriores y no persiste
#  ninguno."
#
# El endpoint envuelve la persistencia en un try/commit/except/rollback. Para
# ejercitar esa rama hay que provocar un fallo real en el commit: se parchea
# Session.commit para que levante una excepción, de modo que la transacción
# quede a medias y el rollback tenga algo que revertir.
# ─────────────────────────────────────────────────────────────────────────────

def test_importar_confirmar_revierte_todo_si_falla_la_persistencia(client, auth_headers, db):
    movimientos = [
        _gasto("2026-03-01T00:00:00", "Adobe Photoshop", 1200, "Software"),
        _gasto("2026-03-02T00:00:00", "AWS EC2", 2800, "Infraestructura"),
        _ingreso("2026-03-03T00:00:00", "Honorarios cliente Acme", 95000),
    ]

    # La BD arranca vacía para este usuario.
    assert client.get("/gastos/", headers=auth_headers).json() == []
    assert client.get("/ingresos/", headers=auth_headers).json() == []

    # El commit falla a mitad de la operación (p. ej. la BD se cae).
    with patch.object(type(db), "commit", side_effect=RuntimeError("BD caída")):
        response = client.post(
            "/importar/confirmar",
            json={"movimientos": movimientos, "mapeo": {}},
            headers=auth_headers,
        )

    # El endpoint informa el fallo y aclara que no quedaron registros parciales.
    assert response.status_code == 500
    assert "revertida" in response.json()["detail"].lower()

    # Ningún registro quedó persistido: ni los que iban antes del fallo.
    assert client.get("/gastos/", headers=auth_headers).json() == []
    assert client.get("/ingresos/", headers=auth_headers).json() == []


def test_importacion_con_fecha_ilegible_no_persiste_nada(client, auth_headers):
    """HU-07: si falla el procesamiento de un registro, no se persiste ninguno.

    Antes, una fecha ilegible se sustituía en silencio por la fecha del día:
    el movimiento entraba igual, pero imputado a otro período fiscal.
    """
    antes_ing = len(client.get("/ingresos/", headers=auth_headers).json())
    antes_gas = len(client.get("/gastos/", headers=auth_headers).json())

    movimientos = [
        {"fecha": "2026-05-04T00:00:00", "descripcion": "Honorarios cliente Orion",
         "monto": 310000.0, "tipo": "ingreso", "categoria": "Servicios"},
        {"fecha": "no-es-una-fecha", "descripcion": "IIBB Percepcion AGIP",
         "monto": 2870.5, "tipo": "gasto", "categoria": "Impuestos"},
        {"fecha": "2026-05-20T00:00:00", "descripcion": "Comision bancaria",
         "monto": 4200.0, "tipo": "gasto", "categoria": "Servicios"},
    ]
    response = client.post(
        "/importar/confirmar",
        json={"movimientos": movimientos, "mapeo": {}},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "IIBB" in response.json()["detail"]

    # Ni el movimiento válido anterior ni el posterior quedaron persistidos.
    assert len(client.get("/ingresos/", headers=auth_headers).json()) == antes_ing
    assert len(client.get("/gastos/", headers=auth_headers).json()) == antes_gas


# ── Consistencia con la carga manual de ingresos ────────────────────────────

MAPEO_BASE = {
    "columna_fecha": "Fecha",
    "columna_descripcion": "Concepto",
    "columna_debito": "Débito",
    "columna_credito": "Crédito",
    "formato_fecha": "%d/%m/%Y",
}


def _movimiento(descripcion="COBRO CLIENTE ZETA", monto=333000.0, tipo="ingreso",
                categoria="Otros", fecha="2026-08-15T00:00:00"):
    return {
        "fecha": fecha, "descripcion": descripcion,
        "monto": monto, "tipo": tipo, "categoria": categoria,
    }


def test_archivo_con_la_misma_fila_dos_veces_marca_los_ingresos(client, auth_headers):
    """Las filas repetidas dentro del propio archivo entran, pero advertidas.

    filtrar_no_duplicados solo descarta lo que ya estaba en la base; dos
    líneas idénticas del mismo archivo la atraviesan. Antes quedaban sin
    marca, así que el filtro "Solo duplicados" no las mostraba aunque fueran
    exactamente el caso que ese filtro tiene que encontrar.
    """
    respuesta = client.post("/importar/confirmar", json={
        "mapeo": MAPEO_BASE,
        "movimientos": [_movimiento(), _movimiento()],
    }, headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json()["ingresos_creados"] == 2
    assert respuesta.json()["ingresos_marcados_duplicados"] == 2

    duplicados = client.get("/ingresos/?solo_duplicados=true", headers=auth_headers)
    assert len(duplicados.json()) == 2


def test_importar_un_ingreso_ya_cargado_a_mano_lo_omite(client, auth_headers):
    # La detección previa a la persistencia sigue siendo la primera defensa.
    client.post("/ingresos/", json={
        "descripcion": "COBRO CLIENTE ZETA", "monto": 333000,
        "categoria": "Otros", "fecha": "2026-08-15T00:00:00",
    }, headers=auth_headers)

    respuesta = client.post("/importar/confirmar", json={
        "mapeo": MAPEO_BASE, "movimientos": [_movimiento()],
    }, headers=auth_headers)
    assert respuesta.json()["ingresos_creados"] == 0
    assert respuesta.json()["omitidos_por_duplicado"] == 1


def test_importar_cuotas_de_un_plan_de_pago_no_marca_nada(client, auth_headers):
    cuotas = ["2026-03-10T00:00:00", "2026-04-10T00:00:00", "2026-05-10T00:00:00"]
    respuesta = client.post("/importar/confirmar", json={
        "mapeo": MAPEO_BASE,
        "movimientos": [
            _movimiento(descripcion="CUOTA PLAN DE PAGO ACME", monto=250000.0, fecha=f)
            for f in cuotas
        ],
    }, headers=auth_headers)
    assert respuesta.json()["ingresos_creados"] == 3
    assert respuesta.json()["ingresos_marcados_duplicados"] == 0


def test_confirmar_rechaza_una_categoria_inventada(client, auth_headers):
    respuesta = client.post("/importar/confirmar", json={
        "mapeo": MAPEO_BASE,
        "movimientos": [_movimiento(categoria="asdasdasd")],
    }, headers=auth_headers)
    assert respuesta.status_code == 422


def test_confirmar_rechaza_una_categoria_de_gasto_en_un_ingreso(client, auth_headers):
    # "Suscripciones" existe para gastos, no para ingresos: los catálogos
    # son distintos y cada tipo se valida contra el suyo.
    respuesta = client.post("/importar/confirmar", json={
        "mapeo": MAPEO_BASE,
        "movimientos": [_movimiento(categoria="Suscripciones")],
    }, headers=auth_headers)
    assert respuesta.status_code == 422


def test_confirmar_acepta_una_categoria_de_gasto_en_un_gasto(client, auth_headers):
    respuesta = client.post("/importar/confirmar", json={
        "mapeo": MAPEO_BASE,
        "movimientos": [_movimiento(
            descripcion="ADOBE CREATIVE CLOUD", monto=32000.0,
            tipo="gasto", categoria="Suscripciones",
        )],
    }, headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json()["gastos_creados"] == 1


# ── Montos en formato argentino y filas defectuosas (revisión M06) ──────────
import pytest
from app.services.csv_service import _parse_monto


@pytest.mark.parametrize("texto, esperado", [
    ("15.000", 15000.0),            # punto de miles, sin decimales
    ("-15.000", -15000.0),
    ("1.250.000", 1250000.0),       # varios puntos de miles
    ("1.234,56", 1234.56),          # formato argentino completo
    ("-3.500,50", -3500.5),
    ("3500,50", 3500.5),            # coma decimal sola
    ("1234.56", 1234.56),           # punto decimal (Mercado Pago, Brubank)
    ("12500.00", 12500.0),
    ("1,234.56", 1234.56),          # formato inglés
    ("1,250,000", 1250000.0),
    ("$ 1.500,00", 1500.0),
    ("(1.234,56)", -1234.56),       # negativo entre paréntesis
    ("1.234,56-", -1234.56),        # negativo con el signo al final
    ("850", 850.0),
    (15000, 15000.0),               # Excel ya entrega números
    (1234.5, 1234.5),
])
def test_parse_monto_formatos(texto, esperado):
    assert _parse_monto(texto) == pytest.approx(esperado)


@pytest.mark.parametrize("texto", ["abc", "", "   ", None, "NaN", "inf", "1.2.3,4,5"])
def test_parse_monto_ilegible_devuelve_none(texto):
    assert _parse_monto(texto) is None


def _preview(client, auth_headers, contenido: bytes, nombre="extracto.csv"):
    return client.post(
        "/importar/preview",
        files={"archivo": (nombre, io.BytesIO(contenido), "text/csv")},
        headers=auth_headers,
    )


def test_preview_lee_montos_con_punto_de_miles(client, auth_headers):
    """Antes "-15.000" se leía como 15 pesos y "1.250.000" desaparecía."""
    csv_bytes = (
        "Fecha;Descripcion;Importe\n"
        "20/09/2026;Supermercado Coto;-15.000\n"
        "21/09/2026;Pago cliente Acme;1.250.000\n"
        "22/09/2026;Uber viaje;-3.500,50\n"
    ).encode()
    data = _preview(client, auth_headers, csv_bytes).json()
    montos = {m["descripcion"]: (m["tipo"], m["monto"]) for m in data["preview"]}
    assert montos == {
        "Supermercado Coto": ("gasto", 15000.0),
        "Pago cliente Acme": ("ingreso", 1250000.0),
        "Uber viaje": ("gasto", 3500.5),
    }


def test_preview_informa_las_filas_que_no_pudo_leer(client, auth_headers):
    csv_bytes = (
        "Fecha,Descripcion,Importe\n"
        "20/09/2026,Supermercado Coto,-15000\n"
        ",Fila sin fecha,-100\n"
        "32/13/2026,Fecha imposible,-300\n"
        "22/09/2026,Monto roto,abc\n"
    ).encode()
    data = _preview(client, auth_headers, csv_bytes).json()
    assert data["total_filas"] == 1
    assert data["resumen"]["omitidas"] == 3
    motivos = {f["fila"]: f["motivo"] for f in data["filas_omitidas"]}
    assert motivos[2] == "sin fecha"
    assert motivos[3].startswith("fecha ilegible")
    assert motivos[4].startswith("importe ilegible")


def test_preview_descripcion_vacia_no_se_convierte_en_nan(client, auth_headers):
    csv_bytes = b"Fecha,Descripcion,Importe\n20/09/2026,,-200\n"
    data = _preview(client, auth_headers, csv_bytes).json()
    assert data["preview"][0]["descripcion"] == "Sin descripción"


def test_preview_recorta_descripciones_mas_largas_que_la_columna(client, auth_headers):
    csv_bytes = ("Fecha,Descripcion,Importe\n20/09/2026," + "x" * 400 + ",-200\n").encode()
    data = _preview(client, auth_headers, csv_bytes).json()
    assert len(data["preview"][0]["descripcion"]) == 255


@pytest.mark.parametrize("cambio", [
    {"monto": -500},
    {"monto": 0},
    {"monto": 10 ** 10},
    {"descripcion": "   "},
    {"descripcion": "x" * 256},
])
def test_confirmar_rechaza_movimientos_invalidos_sin_guardar_nada(client, auth_headers, cambio):
    valido = {"fecha": "2026-09-20T00:00:00", "descripcion": "Cafe", "monto": 850.0,
              "tipo": "gasto", "categoria": "Alimentación"}
    response = client.post("/importar/confirmar", json={
        "movimientos": [valido, {**valido, "descripcion": "Taxi", **cambio}],
        "mapeo": {},
    }, headers=auth_headers)
    assert response.status_code == 422
    assert client.get("/gastos/", headers=auth_headers).json() == [], "no queda nada a medias"


def test_confirmar_rechaza_monto_nan(client, auth_headers):
    cuerpo = ('{"mapeo": {}, "movimientos": [{"fecha": "2026-09-20T00:00:00", "descripcion": "x", '
              '"monto": NaN, "tipo": "gasto", "categoria": "Otros"}]}')
    response = client.post("/importar/confirmar", content=cuerpo,
                           headers={**auth_headers, "Content-Type": "application/json"})
    assert response.status_code == 422
    assert client.get("/gastos/", headers=auth_headers).json() == []
