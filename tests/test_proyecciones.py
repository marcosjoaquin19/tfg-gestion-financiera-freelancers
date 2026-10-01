"""
Tests del módulo de Proyecciones (/proyecciones).

Verifican la generación con Prophet y con el arranque en frío, que solo se
entrene con meses cerrados, que la proyección arranque siempre el mes que
viene, el horizonte acotado, el método informado y la serie histórica.

El "hoy" se fija con el fixture `hoy` para que los tests no dependan del
calendario: la regla de meses cerrados depende de en qué mes estamos.
"""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

import app.services.prophet_service as ps

HOY = datetime(2026, 9, 27)
# Con HOY en septiembre: meses cerrados hasta agosto, septiembre en curso,
# la proyección va de octubre 2026 a marzo 2027.
MESES_ESPERADOS = ["2026-10", "2026-11", "2026-12", "2027-01", "2027-02", "2027-03"]

INGRESO_BASE = {"descripcion": "Honorarios", "monto": 100000, "categoria": "Servicios", "fecha": "2026-01-10T12:00:00"}


@pytest.fixture(autouse=True)
def hoy(monkeypatch):
    class Fija(datetime):
        @classmethod
        def now(cls, tz=None):
            return HOY.replace(tzinfo=tz) if tz else HOY
    monkeypatch.setattr(ps, "datetime", Fija)


def _ingreso(client, headers, anio, mes, monto, dia=10):
    r = client.post(
        "/ingresos/",
        json={**INGRESO_BASE, "fecha": f"{anio}-{mes:02d}-{dia:02d}T12:00:00", "monto": monto},
        headers=headers,
    )
    assert r.status_code == 201, r.text


def _historia(client, headers, meses, montos_por_mes=(1_000_000, 1_100_000, 900_000)):
    """Tres cobros por mes en cada (anio, mes) indicado."""
    for anio, mes in meses:
        for k, monto in enumerate(montos_por_mes):
            _ingreso(client, headers, anio, mes, monto, dia=3 + k * 4)


def _generar(client, headers, periodos=6):
    return client.post("/proyecciones/generar", json={"periodos": periodos}, headers=headers)


def _meses(data):
    return [p["fecha_proyeccion"][:7] for p in data]


MAYO_A_AGOSTO = [(2026, 5), (2026, 6), (2026, 7), (2026, 8)]


# --- Prophet y mes en curso -------------------------------------------------

def test_prophet_con_historia_suficiente(client, auth_headers):
    _historia(client, auth_headers, MAYO_A_AGOSTO)  # 12 ingresos en 4 meses cerrados
    r = _generar(client, auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert _meses(data) == MESES_ESPERADOS
    assert all(p["metodo"] == "prophet" for p in data)
    for p in data:
        assert 0 <= p["monto_lower"] <= p["monto_proyectado"] <= p["monto_upper"]


def test_mes_en_curso_no_hunde_la_proyeccion(client, auth_headers):
    # Regresión: un único cobro chico en el mes en curso se leía como un mes
    # completo de $200.000 y Prophet proyectaba una caída hasta $0.
    _historia(client, auth_headers, MAYO_A_AGOSTO)
    sin_parcial = _generar(client, auth_headers).json()

    _ingreso(client, auth_headers, 2026, 9, 200_000, dia=2)
    con_parcial = _generar(client, auth_headers).json()

    assert [p["monto_proyectado"] for p in con_parcial] == [p["monto_proyectado"] for p in sin_parcial]
    assert all(p["monto_proyectado"] > 2_000_000 for p in con_parcial)


def test_prophet_es_reproducible(client, auth_headers):
    _historia(client, auth_headers, MAYO_A_AGOSTO)
    primera = _generar(client, auth_headers).json()
    segunda = _generar(client, auth_headers).json()
    campos = ("monto_lower", "monto_proyectado", "monto_upper")
    assert [[p[c] for c in campos] for p in primera] == [[p[c] for c in campos] for p in segunda]


def test_dos_meses_no_alcanzan_para_prophet(client, auth_headers):
    # 12 ingresos (supera el mínimo de 10) pero en solo 2 meses cerrados: una
    # recta por dos puntos no es una tendencia → arranque en frío.
    _historia(client, auth_headers, [(2026, 7), (2026, 8)], montos_por_mes=(500_000,) * 6)
    data = _generar(client, auth_headers).json()
    assert all(p["metodo"] == "media_movil" for p in data)
    assert all(p["monto_proyectado"] == 3_000_000 for p in data)


def test_diez_ingresos_contando_el_mes_en_curso_no_alcanzan(client, auth_headers):
    # 9 ingresos en meses cerrados + 3 en el mes en curso: para el umbral de
    # Prophet solo cuentan los de meses cerrados.
    _historia(client, auth_headers, [(2026, 6), (2026, 7), (2026, 8)])
    _historia(client, auth_headers, [(2026, 9)])
    data = _generar(client, auth_headers).json()
    assert all(p["metodo"] == "media_movil" for p in data)


# --- Arranque en frío -------------------------------------------------------

def test_media_movil_promedia_totales_mensuales(client, auth_headers):
    # Tres cobros de $100.000 por mes son $300.000 por mes, no $100.000:
    # antes se promediaban los cobros sueltos y se subestimaba el ingreso.
    _historia(client, auth_headers, [(2026, 7), (2026, 8)], montos_por_mes=(100_000,) * 3)
    data = _generar(client, auth_headers).json()
    assert all(p["metodo"] == "media_movil" for p in data)
    assert all(p["monto_proyectado"] == 300_000 for p in data)


def test_media_movil_usa_los_ultimos_tres_meses(client, auth_headers):
    for mes, monto in [(4, 100_000), (5, 100_000), (6, 400_000), (7, 500_000), (8, 600_000)]:
        _ingreso(client, auth_headers, 2026, mes, monto)
    data = _generar(client, auth_headers).json()
    assert data[0]["metodo"] == "media_movil"
    assert data[0]["monto_proyectado"] == 500_000          # (400k + 500k + 600k) / 3
    assert data[0]["monto_lower"] == 400_000               # ± 1 desvío (100k)
    assert data[0]["monto_upper"] == 600_000


def test_un_solo_mes_cerrado_banda_del_20_por_ciento(client, auth_headers):
    _ingreso(client, auth_headers, 2026, 8, 1_000_000)
    data = _generar(client, auth_headers).json()
    assert data[0]["metodo"] == "media_movil"
    assert (data[0]["monto_lower"], data[0]["monto_proyectado"], data[0]["monto_upper"]) == (800_000, 1_000_000, 1_200_000)


def test_historial_en_un_solo_mes(client, auth_headers):
    # Regresión: con 10+ ingresos concentrados en un único mes el DataFrame
    # mensual tenía una sola fila y el fit de Prophet fallaba (500).
    for i in range(12):
        _ingreso(client, auth_headers, 2026, 8, 90_000 + i * 500, dia=i + 1)
    r = _generar(client, auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert len(data) == 6
    assert all(p["metodo"] == "media_movil" and p["monto_proyectado"] > 0 for p in data)


def test_solo_ingresos_del_mes_en_curso(client, auth_headers):
    _ingreso(client, auth_headers, 2026, 9, 400_000, dia=3)
    _ingreso(client, auth_headers, 2026, 9, 100_000, dia=20)
    data = _generar(client, auth_headers).json()
    assert _meses(data) == MESES_ESPERADOS
    assert all(p["metodo"] == "mes_en_curso" and p["monto_proyectado"] == 500_000 for p in data)


def test_usuario_sin_ingresos(client, auth_headers):
    r = _generar(client, auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert _meses(data) == MESES_ESPERADOS
    assert all(p["metodo"] == "sin_datos" and p["monto_proyectado"] == 0 for p in data)


def test_ingresos_con_fecha_futura_no_entran(client, auth_headers):
    # La carga no bloquea fechas futuras (decisión de M02): la proyección las
    # ignora, porque todavía no son historia.
    _ingreso(client, auth_headers, 2027, 1, 9_000_000)
    data = _generar(client, auth_headers).json()
    assert all(p["metodo"] == "sin_datos" for p in data)


# --- Siempre desde el mes que viene ------------------------------------------

def test_historial_viejo_no_proyecta_meses_pasados(client, auth_headers):
    # Regresión: con el último ingreso en junio, la proyección arrancaba en
    # julio y mostraba julio-septiembre (ya pasados) como futuro.
    _historia(client, auth_headers, [(2026, 2), (2026, 3), (2026, 4), (2026, 5), (2026, 6)])
    data = _generar(client, auth_headers).json()
    assert data[0]["metodo"] == "prophet"
    assert _meses(data) == MESES_ESPERADOS


def test_historial_viejo_media_movil_tambien_arranca_el_mes_que_viene(client, auth_headers):
    _ingreso(client, auth_headers, 2025, 11, 500_000)
    data = _generar(client, auth_headers).json()
    assert data[0]["metodo"] == "media_movil"
    assert _meses(data) == MESES_ESPERADOS


# --- Horizonte ---------------------------------------------------------------

@pytest.mark.parametrize("periodos", [0, -3, 7, 120])
def test_periodos_fuera_de_rango(client, auth_headers, periodos):
    assert _generar(client, auth_headers, periodos).status_code == 422


def test_periodos_invalido_no_borra_la_proyeccion_anterior(client, auth_headers):
    # Antes, periodos=0 borraba la proyección guardada sin generar otra.
    _ingreso(client, auth_headers, 2026, 8, 1_000_000)
    _generar(client, auth_headers)
    _generar(client, auth_headers, 0)
    assert len(client.get("/proyecciones/", headers=auth_headers).json()) == 6


def test_periodos_menor_a_seis(client, auth_headers):
    _historia(client, auth_headers, MAYO_A_AGOSTO)
    data = _generar(client, auth_headers, 3).json()
    assert _meses(data) == MESES_ESPERADOS[:3]


def test_periodos_por_defecto_son_seis(client, auth_headers):
    r = client.post("/proyecciones/generar", json={}, headers=auth_headers)
    assert r.status_code == 201
    assert len(r.json()) == 6


def test_periodos_no_numerico(client, auth_headers):
    assert client.post("/proyecciones/generar", json={"periodos": "seis"}, headers=auth_headers).status_code == 422


# --- Reemplazo, listado y límites de Prophet ---------------------------------

def test_generar_reemplaza_las_anteriores(client, auth_headers):
    _historia(client, auth_headers, MAYO_A_AGOSTO)
    _generar(client, auth_headers)
    _generar(client, auth_headers)
    listado = client.get("/proyecciones/", headers=auth_headers).json()
    assert len(listado) == 6
    assert all(p["metodo"] == "prophet" for p in listado)


def test_montos_negativos_de_prophet_se_recortan_a_cero(client, auth_headers):
    # Una tendencia descendente puede dar valores negativos: un ingreso
    # negativo no tiene sentido, se recorta a $0.
    _historia(client, auth_headers, MAYO_A_AGOSTO)
    forecast = pd.DataFrame({
        "ds": pd.date_range("2026-09-01", periods=7, freq="MS"),
        "yhat": [-50_000.0] * 7,
        "yhat_lower": [-90_000.0] * 7,
        "yhat_upper": [20_000.0] * 7,
    })
    with patch("app.services.prophet_service.Prophet") as MockProphet:
        instancia = MagicMock()
        instancia.predict.return_value = forecast
        MockProphet.return_value = instancia
        data = _generar(client, auth_headers).json()

    assert _meses(data) == MESES_ESPERADOS  # descarta septiembre (mes en curso)
    assert all(p["monto_proyectado"] == 0 and p["monto_lower"] == 0 and p["monto_upper"] == 20_000 for p in data)


def test_listar_proyecciones_vacio(client, auth_headers):
    response = client.get("/proyecciones/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_listar_calcula_la_proyeccion_si_todavia_no_hay(client, auth_headers):
    # Regresión: con el demo recién sembrado, el Dashboard pedía la lista antes
    # de que Monotributo o Recomendaciones la calcularan y mostraba
    # "Proyección próx. mes: $ 0". Con ingresos cargados, listar ya la calcula.
    _historia(client, auth_headers, MAYO_A_AGOSTO)
    data = client.get("/proyecciones/", headers=auth_headers).json()
    assert len(data) == 6
    assert data[0]["monto_proyectado"] > 0


def test_listar_no_recalcula_si_nada_cambio(client, auth_headers):
    _historia(client, auth_headers, MAYO_A_AGOSTO)
    ids = [p["id"] for p in client.get("/proyecciones/", headers=auth_headers).json()]
    assert [p["id"] for p in client.get("/proyecciones/", headers=auth_headers).json()] == ids


def test_proyecciones_sin_auth(client):
    assert client.get("/proyecciones/").status_code == 401
    assert client.post("/proyecciones/generar", json={"periodos": 6}).status_code == 401
    assert client.get("/proyecciones/historico").status_code == 401


# --- Serie histórica (/proyecciones/historico) -------------------------------

def test_historico_es_la_serie_de_entrenamiento(client, auth_headers):
    # mayo, junio y agosto con datos; julio sin cobros → cuenta como $0.
    # Septiembre (en curso) va aparte y no se rellenan meses después de agosto.
    _ingreso(client, auth_headers, 2026, 5, 1_000_000)
    _ingreso(client, auth_headers, 2026, 6, 1_200_000)
    _ingreso(client, auth_headers, 2026, 8, 900_000)
    _ingreso(client, auth_headers, 2026, 9, 300_000)

    h = client.get("/proyecciones/historico", headers=auth_headers).json()
    assert [(m["mes"][:7], m["total"]) for m in h["meses"]] == [
        ("2026-05", 1_000_000), ("2026-06", 1_200_000), ("2026-07", 0), ("2026-08", 900_000),
    ]
    assert h["mes_en_curso"][:7] == "2026-09"
    assert h["total_mes_en_curso"] == 300_000


def test_mes_sin_ingresos_baja_el_promedio(client, auth_headers):
    # El hueco de julio pesa en el arranque en frío: (600k + 0 + 600k) / 3.
    _ingreso(client, auth_headers, 2026, 6, 600_000)
    _ingreso(client, auth_headers, 2026, 8, 600_000)
    data = _generar(client, auth_headers).json()
    assert data[0]["monto_proyectado"] == 400_000


def test_historico_no_muestra_ingresos_de_otro_usuario(client, auth_headers):
    _ingreso(client, auth_headers, 2026, 8, 900_000)
    client.post("/auth/register", json={"nombre": "Otra", "email": "otra@test.com", "password": "Prueba1234"})
    token = client.post("/auth/login", data={"username": "otra@test.com", "password": "Prueba1234"}).json()["access_token"]
    h = client.get("/proyecciones/historico", headers={"Authorization": f"Bearer {token}"}).json()
    assert h["meses"] == [] and h["total_mes_en_curso"] == 0


# ── Casos bisagra de la revisión final ───────────────────────────────────────

def test_si_prophet_falla_se_usa_la_media_movil(client, auth_headers, monkeypatch):
    _historia(client, auth_headers, [(2026, 5), (2026, 6), (2026, 7), (2026, 8)])

    def falla(*a, **k):
        raise RuntimeError("el optimizador no convergió")
    monkeypatch.setattr(ps, "_proyecciones_prophet", falla)
    r = _generar(client, auth_headers)
    assert r.status_code == 201
    # Media móvil, pero con su propio nombre: no es falta de datos y la
    # pantalla no tiene que explicarlo como arranque en frío.
    assert {p["metodo"] for p in r.json()} == {"respaldo"}
    assert _meses(r.json()) == MESES_ESPERADOS
    assert r.json()[0]["monto_proyectado"] == 3_000_000     # promedio de jun, jul y ago


def test_mes_en_curso_con_el_calendario_de_argentina(monkeypatch):
    # 30/09 a las 23:30 en Argentina ya es 1/10 en UTC: el mes en curso tiene
    # que seguir siendo septiembre.
    from datetime import timezone
    instante = datetime(2026, 10, 1, 2, 30, tzinfo=timezone.utc)

    class Reloj(datetime):
        @classmethod
        def now(cls, tz=None):
            return instante.astimezone(tz) if tz else instante.replace(tzinfo=None)
    monkeypatch.setattr(ps, "datetime", Reloj)
    assert ps.inicio_mes_en_curso() == datetime(2026, 9, 1)
