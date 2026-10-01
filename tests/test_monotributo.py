"""
Tests del módulo de Monotributo (/monotributo).

Verifican el cálculo de la facturación de 12 meses, el porcentaje del límite
consumido, el estado de recategorización y la actualización de categoría.
"""

import pytest


@pytest.fixture(autouse=True)
def seed_categorias(client):
    from decimal import Decimal
    from datetime import date
    from app.models.categoria_monotributo import CategoriaMonotributo
    from app.database import get_db
    from app.main import app

    db = next(app.dependency_overrides[get_db]())
    for letra, limite, cuota in [
        ("A", Decimal("1000000"), Decimal("5000")),
        ("B", Decimal("1500000"), Decimal("6000")),
    ]:
        db.add(CategoriaMonotributo(
            letra=letra,
            limite_anual=limite,
            cuota_mensual=cuota,
            actividad="servicios",
            fecha_vigencia=date(2024, 1, 1),
            activa=True,
        ))
    db.commit()


def test_estado_sin_categoria(client, auth_headers):
    response = client.get("/monotributo/estado", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("sin_categoria") is True


def test_actualizar_categoria(client, auth_headers):
    response = client.patch(
        "/monotributo/categoria",
        json={"categoria_monotributo": "A"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["categoria_monotributo"] == "A"


def test_estado_con_categoria(client, auth_headers):
    client.patch(
        "/monotributo/categoria",
        json={"categoria_monotributo": "B"},
        headers=auth_headers,
    )
    response = client.get("/monotributo/estado", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "categoria_actual" in data
    assert "limite_anual" in data
    assert "cuota_mensual" in data


def test_pago_monotributo(client, auth_headers):
    response = client.get("/monotributo/pago", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pagado" in data


# ── Facturación móvil 12 meses (sugerencia del docente) ──────────────────────

def test_facturacion_12_meses_sin_auth(client):
    assert client.get("/monotributo/facturacion-12-meses").status_code == 401


def test_facturacion_12_meses_vacio(client, auth_headers):
    response = client.get("/monotributo/facturacion-12-meses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["facturacion_12_meses"] == 0
    assert data["categoria"] is None


def test_facturacion_12_meses_excluye_ingresos_de_hace_mas_de_un_anio(client, auth_headers):
    # Cargamos un ingreso reciente y otro de hace más de un año. El cálculo
    # AFIP es ventana móvil de 12 meses, así que el viejo no debe contar.
    from datetime import datetime, timedelta
    reciente = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
    antiguo = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%S")

    client.post("/ingresos/", json={
        "descripcion": "Reciente", "monto": 5000,
        "categoria": "Desarrollo", "fecha": reciente,
    }, headers=auth_headers)
    client.post("/ingresos/", json={
        "descripcion": "Antiguo", "monto": 9999,
        "categoria": "Desarrollo", "fecha": antiguo,
    }, headers=auth_headers)

    response = client.get("/monotributo/facturacion-12-meses", headers=auth_headers)
    assert response.json()["facturacion_12_meses"] == 5000


def test_facturacion_12_meses_incluye_categoria_y_porcentaje(client, auth_headers):
    # Si el usuario tiene categoría seteada, la respuesta agrega el
    # porcentaje del límite anual ya consumido por la facturación móvil.
    client.patch(
        "/monotributo/categoria",
        json={"categoria_monotributo": "A"},
        headers=auth_headers,
    )

    # El día de hoy en Argentina, como lo manda la pantalla (con la hora UTC,
    # entre las 21 h y la medianoche el cobro quedaba fechado mañana).
    from datetime import datetime
    from zoneinfo import ZoneInfo
    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime("%Y-%m-%d")
    client.post("/ingresos/", json={
        "descripcion": "Cobro", "monto": 100000,
        "categoria": "Servicios", "fecha": hoy,
    }, headers=auth_headers)

    data = client.get("/monotributo/facturacion-12-meses", headers=auth_headers).json()
    assert data["facturacion_12_meses"] == 100000
    assert data["categoria"]["categoria"] == "A"
    assert data["categoria"]["limite_anual"] == 1_000_000.0
    assert data["categoria"]["porcentaje_usado"] == 10.0


def test_pago_monotributo_valida_monto_cuota(client, auth_headers):
    # Regresión: cualquier gasto de categoría "Monotributo" contaba como
    # cuota pagada sin importar el monto. Ahora el registro tiene que cubrir
    # la cuota de la categoría (tolerancia 1%); un registro menor se informa
    # como pago parcial y el estado sigue siendo impago.
    client.patch(
        "/monotributo/categoria",
        json={"categoria_monotributo": "A"},  # cuota fixture: 5000
        headers=auth_headers,
    )
    fecha = _dia_del_mes_en_curso(3)

    # Pago parcial: no cubre la cuota.
    client.post(
        "/gastos/",
        json={"descripcion": "Pago monotributo parcial", "monto": 1200, "categoria": "Monotributo", "fecha": fecha},
        headers=auth_headers,
    )
    data = client.get("/monotributo/pago", headers=auth_headers).json()
    assert data["pagado"] is False
    assert data["pago_parcial"] is True
    assert data["monto_esperado"] == 5000.0
    assert data["gasto_encontrado"]["monto"] == 1200.0

    # Pago completo: cubre la cuota → pagado.
    client.post(
        "/gastos/",
        json={"descripcion": "Pago monotributo cuota", "monto": 5000, "categoria": "Monotributo", "fecha": fecha},
        headers=auth_headers,
    )
    data = client.get("/monotributo/pago", headers=auth_headers).json()
    assert data["pagado"] is True
    assert data["pago_parcial"] is False


def _dia_del_mes_en_curso(dia: int) -> str:
    # Con el calendario de Argentina, como la API: con la hora UTC, entre las
    # 21 h y la medianoche del último día el "mes en curso" ya era el siguiente.
    from datetime import datetime
    from zoneinfo import ZoneInfo
    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires"))
    return f"{hoy.year}-{hoy.month:02d}-{dia:02d}"


def _gasto_monotributo(client, headers, monto, dia):
    r = client.post("/gastos/", json={"descripcion": "Pago monotributo", "monto": monto,
                                      "categoria": "Monotributo", "fecha": _dia_del_mes_en_curso(dia)}, headers=headers)
    assert r.status_code == 201, r.text


def test_cuota_en_dos_pagos_que_juntos_la_cubren(client, auth_headers):
    # Regresión: ningún pago por separado cubría la cuota, así que figuraba
    # "parcial" y la auditoría avisaba que no estaba paga.
    client.patch("/monotributo/categoria", json={"categoria_monotributo": "A"}, headers=auth_headers)
    _gasto_monotributo(client, auth_headers, 2500, dia=2)
    data = client.get("/monotributo/pago", headers=auth_headers).json()
    assert (data["pagado"], data["pago_parcial"], data["total_registrado"]) == (False, True, 2500)
    aud = client.post("/alertas/ejecutar-auditoria", headers=auth_headers).json()
    assert aud["detalle"]["monotributo_impago"] == 1
    alerta = client.get("/alertas/", headers=auth_headers).json()[0]["descripcion"]
    assert "Lo registrado en el mes ($ 2.500) no cubre la cuota" in alerta

    _gasto_monotributo(client, auth_headers, 2500, dia=3)
    data = client.get("/monotributo/pago", headers=auth_headers).json()
    assert (data["pagado"], data["pago_parcial"], data["total_registrado"]) == (True, False, 5000)
    aud = client.post("/alertas/ejecutar-auditoria", headers=auth_headers).json()
    assert aud["detalle"]["monotributo_impago"] == 0


def test_cuota_justo_en_el_99_por_ciento(client, auth_headers):
    # Borde de la tolerancia del 1 %: con la cuota A de $ 5.000, $ 4.949,99
    # es un pago parcial y $ 4.950,00 (el 99 % justo) ya cuenta como pagada.
    client.patch("/monotributo/categoria", json={"categoria_monotributo": "A"}, headers=auth_headers)
    _gasto_monotributo(client, auth_headers, 4949.99, dia=2)
    data = client.get("/monotributo/pago", headers=auth_headers).json()
    assert (data["pagado"], data["pago_parcial"]) == (False, True)

    _gasto_monotributo(client, auth_headers, 0.01, dia=3)
    data = client.get("/monotributo/pago", headers=auth_headers).json()
    assert (data["pagado"], data["pago_parcial"], data["total_registrado"]) == (True, False, 4950)
