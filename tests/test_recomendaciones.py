"""
Tests de las recomendaciones (GET /recomendaciones, HU-12).

Verifican los criterios de la HU-12 —entre 3 y 5 sugerencias, reglas locales,
alertas + tendencia de ingresos + proyección consideradas a la vez— y las
reglas de redacción del proyecto: tono de sugerencia, inversión a elección del
usuario y ninguna cifra que no salga de los datos (cada monto del texto tiene
que figurar en su "dato").

El reloj se fija el 27-sep-2026: septiembre es el mes en curso y agosto el
último mes cerrado.
"""

import re
from datetime import datetime
from decimal import Decimal

import pytest

import app.services.ia_service as ia
import app.services.monotributo_service as ms
import app.services.prophet_service as ps

HOY = datetime(2026, 9, 27, 12)

ESCALA = [("A", "1200000", "10000"), ("B", "1800000", "12000"), ("C", "2400000", "14000"),
          ("D", "3000000", "16000"), ("E", "4500000", "20000"), ("K", "6000000", "50000")]


@pytest.fixture(autouse=True)
def entorno(client, monkeypatch):
    from datetime import date
    from app.database import get_db
    from app.main import app
    from app.models.categoria_monotributo import CategoriaMonotributo

    db = next(app.dependency_overrides[get_db]())
    for letra, limite, cuota in ESCALA:
        db.add(CategoriaMonotributo(letra=letra, limite_anual=Decimal(limite), cuota_mensual=Decimal(cuota),
                                    actividad="servicios", fecha_vigencia=date(2026, 8, 1), activa=True))
    db.commit()

    class Fija(datetime):
        @classmethod
        def now(cls, tz=None):
            return HOY.replace(tzinfo=tz) if tz else HOY
    monkeypatch.setattr(ps, "datetime", Fija)
    monkeypatch.setattr(ms, "datetime", Fija)

    # Ninguna recomendación puede salir a un servicio externo.
    def prohibido(*a, **k):
        raise AssertionError("las recomendaciones no deben usar Groq")
    monkeypatch.setattr(ia, "Groq", prohibido)


# --- Helpers -------------------------------------------------------------------

def _ingreso(c, h, mes, monto, anio=2026, dia=10):
    r = c.post("/ingresos/", json={"descripcion": "Honorarios", "monto": monto, "categoria": "Servicios",
                                   "fecha": f"{anio}-{mes:02d}-{dia:02d}T12:00:00"}, headers=h)
    assert r.status_code == 201, r.text


def _gasto(c, h, mes, monto, cat="Software", dia=10, desc="Gasto"):
    r = c.post("/gastos/", json={"descripcion": desc, "monto": monto, "categoria": cat,
                                 "fecha": f"2026-{mes:02d}-{dia:02d}T12:00:00"}, headers=h)
    assert r.status_code == 201, r.text


def _factura(c, h, cliente, monto, emision, vencimiento):
    r = c.post("/facturas/", json={"cliente_nombre": cliente, "descripcion": "Servicio", "monto": monto,
                                   "fecha_emision": f"{emision}T12:00:00",
                                   "fecha_vencimiento": f"{vencimiento}T12:00:00"}, headers=h)
    assert r.status_code == 201, r.text


def _categoria(c, h, letra="A"):
    assert c.patch("/monotributo/categoria", json={"categoria_monotributo": letra}, headers=h).status_code == 200


def _recs(c, h):
    r = c.get("/recomendaciones/", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _reglas(data):
    return [d["regla"] for d in data["detalle"]]


def _montos(texto):
    return set(re.findall(r"\$ [\d.]+,\d{2}", texto))


# --- Escenarios reutilizables ----------------------------------------------------

def escenario_sin_datos(c, h):
    pass


def escenario_un_cobro(c, h):
    _ingreso(c, h, 9, 50_000, dia=3)


def escenario_solo_gastos(c, h):
    _gasto(c, h, 8, 40_000)


def escenario_en_orden(c, h):
    _categoria(c, h, "A")
    for mes in (6, 7, 8):
        _ingreso(c, h, mes, 100_000)
        _gasto(c, h, mes, 30_000, dia=12)


def escenario_muchas_senales(c, h):
    _categoria(c, h, "A")
    for mes, monto in [(5, 900_000), (6, 800_000), (7, 300_000), (8, 200_000)]:
        _ingreso(c, h, mes, monto)
    for cat, antes, ahora in [("Software", 50_000, 120_000), ("Marketing", 40_000, 100_000)]:
        _gasto(c, h, 8, antes, cat)
        _gasto(c, h, 9, ahora, cat, dia=5)
    _gasto(c, h, 8, 700_000, "Hardware", dia=1)
    _gasto(c, h, 8, 25_000, "Transporte", dia=14, desc="Uber")
    _gasto(c, h, 8, 25_000, "Transporte", dia=15, desc="Uber")            # duplicado
    _factura(c, h, "Estudio Pérez", 200_000, "2026-07-01", "2026-08-01")  # vencida
    _factura(c, h, "Kiosco Sur", 150_000, "2026-09-01", "2026-12-01")     # pendiente
    c.post("/alertas/ejecutar-auditoria", headers=h)


ESCENARIOS = [escenario_sin_datos, escenario_un_cobro, escenario_solo_gastos,
              escenario_en_orden, escenario_muchas_senales]


# --- HU-12: cantidad, reglas locales, insumos simultáneos --------------------------

@pytest.mark.parametrize("escenario", ESCENARIOS, ids=lambda e: e.__name__)
def test_siempre_entre_3_y_5(client, auth_headers, escenario):
    escenario(client, auth_headers)
    data = _recs(client, auth_headers)
    assert 3 <= len(data["recomendaciones"]) <= 5
    assert data["generado_con_ia"] is False


def test_muchas_senales_se_recortan_a_5_por_urgencia(client, auth_headers):
    escenario_muchas_senales(client, auth_headers)
    data = _recs(client, auth_headers)
    assert len(data["detalle"]) == 5
    prioridades = [d["prioridad"] for d in data["detalle"]]
    assert prioridades == sorted(prioridades)
    assert data["detalle"][0]["regla"] == "facturas_vencidas"


def test_considera_alertas_tendencia_y_proyeccion_a_la_vez(client, auth_headers):
    escenario_muchas_senales(client, auth_headers)
    reglas = _reglas(_recs(client, auth_headers))
    assert "alertas_auditoria" in reglas
    assert "ingresos_en_baja" in reglas
    assert any(r.startswith("fiscal_") for r in reglas)      # usa la proyección vía el estado fiscal


def test_caida_de_ingresos_y_riesgo_fiscal_no_se_ignoran(client, auth_headers):
    # Regresión: con ingresos 3M → 2M → 1M → 0,3M y semáforo en riesgo, la
    # única recomendación era "te quedó superávit, invertí en plazo fijo".
    _categoria(client, auth_headers, "E")
    for mes, monto in [(5, 3_000_000), (6, 2_000_000), (7, 1_000_000), (8, 300_000)]:
        _ingreso(client, auth_headers, mes, monto)
    data = _recs(client, auth_headers)
    reglas = _reglas(data)
    assert "ingresos_en_baja" in reglas
    assert any(r.startswith("fiscal_") for r in reglas)
    baja = next(d for d in data["detalle"] if d["regla"] == "ingresos_en_baja")
    assert "julio y agosto de 2026" in baja["texto"] and "$ 650.000,00" in baja["texto"]
    assert "mayo y junio de 2026" in baja["texto"] and "$ 2.500.000,00" in baja["texto"]
    assert "74 %" in baja["texto"]
    if "resultado_superavit" in reglas:
        assert reglas.index("ingresos_en_baja") < reglas.index("resultado_superavit")


def test_son_deterministas(client, auth_headers):
    escenario_muchas_senales(client, auth_headers)
    assert _recs(client, auth_headers) == _recs(client, auth_headers)


# --- Nada inventado ----------------------------------------------------------------

def test_usuario_sin_datos_no_recibe_diagnosticos(client, auth_headers):
    # Regresión: decía "tu situación está en orden… gastos controlados" sin
    # un solo dato cargado.
    data = _recs(client, auth_headers)
    assert _reglas(data) == ["sin_ingresos", "sin_categoria", "sin_gastos"]
    for texto in data["recomendaciones"]:
        assert "$" not in texto and "en orden" not in texto and "controlados" not in texto


@pytest.mark.parametrize("escenario", ESCENARIOS, ids=lambda e: e.__name__)
def test_cada_monto_del_texto_figura_en_su_dato(client, auth_headers, escenario):
    escenario(client, auth_headers)
    for d in _recs(client, auth_headers)["detalle"]:
        assert d["regla"] and d["dato"]
        assert _montos(d["texto"]) <= _montos(d["dato"]), d


def test_superavit_con_montos_exactos_y_sin_el_mes_en_curso(client, auth_headers):
    escenario_en_orden(client, auth_headers)
    _ingreso(client, auth_headers, 9, 5_000_000, dia=2)          # mes en curso: no entra
    sup = next(d for d in _recs(client, auth_headers)["detalle"] if d["regla"] == "resultado_superavit")
    assert sup["texto"].startswith("Entre junio y agosto de 2026 te quedó un superávit promedio de $ 70.000,00 por mes")
    assert "cobraste $ 100.000,00 y gastaste $ 30.000,00" in sup["texto"]
    assert "3 meses cerrados: ingresos $ 300.000,00" in sup["dato"]


def test_deficit_nombra_los_rubros_de_mayor_gasto(client, auth_headers):
    _ingreso(client, auth_headers, 8, 100_000)
    _gasto(client, auth_headers, 8, 250_000, "Hardware")
    _gasto(client, auth_headers, 8, 50_000, "Software", dia=12)
    d = next(d for d in _recs(client, auth_headers)["detalle"] if d["regla"] == "resultado_deficit")
    assert d["prioridad"] == 2
    # Con un solo mes cerrado no se habla de "promedio por mes".
    assert d["texto"].startswith("En agosto de 2026 gastaste $ 300.000,00 y cobraste $ 100.000,00: un déficit de $ 200.000,00.")
    assert "por mes" not in d["texto"]
    assert "(Hardware y Software)" in d["texto"]
    assert "Hardware $ 250.000,00; Software $ 50.000,00" in d["dato"]


# --- Redacción: siempre sugerencia ---------------------------------------------------

def test_superavit_sugiere_invertir_a_eleccion_del_usuario(client, auth_headers):
    escenario_en_orden(client, auth_headers)
    sup = next(d for d in _recs(client, auth_headers)["detalle"] if d["regla"] == "resultado_superavit")
    texto = sup["texto"]
    assert "Podrías destinar ese excedente" in texto
    assert "en el instrumento que prefieras" in texto
    for opcion in ("plazo fijo", "fondos comunes de inversión", "acciones"):
        assert opcion in texto
    assert "según tu perfil de riesgo" in texto
    assert "10%" not in texto and "20%" not in texto                # sin metas que no salen de los datos


@pytest.mark.parametrize("escenario", ESCENARIOS, ids=lambda e: e.__name__)
def test_tono_de_sugerencia_y_plurales(client, auth_headers, escenario):
    escenario(client, auth_headers)
    for texto in _recs(client, auth_headers)["recomendaciones"]:
        assert "(s)" not in texto
        assert not re.search(r"\b(Invertí|Contactá|Debés|Tenés que|Hacé|Revisá|Ajustá)\b", texto), texto


def test_singular_en_una_factura_vencida(client, auth_headers):
    _factura(client, auth_headers, "Estudio Pérez", 200_000, "2026-07-01", "2026-08-01")
    d = next(d for d in _recs(client, auth_headers)["detalle"] if d["regla"] == "facturas_vencidas")
    assert d["texto"].startswith("Tenés 1 factura vencida sin cobrar por $ 200.000,00. Te sugerimos contactar a ese cliente")
    assert "Estudio Pérez, $ 200.000,00, venció el 01/08/2026" in d["dato"]


# --- Reglas puntuales -----------------------------------------------------------------

def test_alertas_no_repiten_facturas_ni_monotributo(client, auth_headers):
    _categoria(client, auth_headers, "A")
    _factura(client, auth_headers, "Estudio Pérez", 200_000, "2026-07-01", "2026-08-01")
    _gasto(client, auth_headers, 8, 25_000, "Transporte", dia=14)
    _gasto(client, auth_headers, 8, 25_000, "Transporte", dia=15)
    client.post("/alertas/ejecutar-auditoria", headers=auth_headers)   # genera también factura + monotributo
    d = next(d for d in _recs(client, auth_headers)["detalle"] if d["regla"] == "alertas_auditoria")
    assert d["texto"].startswith("La auditoría detectó 1 posible gasto duplicado sin revisar")
    assert "1 alerta pendiente" in d["dato"]


def test_aumentos_de_gasto_van_en_una_sola_recomendacion(client, auth_headers):
    for cat, antes, ahora in [("Software", 50_000, 120_000), ("Marketing", 40_000, 100_000), ("Hardware", 30_000, 90_000)]:
        _gasto(client, auth_headers, 8, antes, cat)
        _gasto(client, auth_headers, 9, ahora, cat, dia=5)
    data = _recs(client, auth_headers)
    d = next(d for d in data["detalle"] if d["regla"] == "gastos_en_aumento")
    assert _reglas(data).count("gastos_en_aumento") == 1
    assert "Hardware (+200 %), Marketing (+150 %) y Software (+140 %)" in d["texto"]
    assert "Hardware: $ 90.000,00 en septiembre contra $ 30.000,00 en agosto" in d["dato"]


def test_cuota_impaga_y_estado_fiscal_en_una_recomendacion(client, auth_headers):
    _categoria(client, auth_headers, "A")
    for mes in (6, 7, 8):
        _ingreso(client, auth_headers, mes, 300_000)
    d = next(d for d in _recs(client, auth_headers)["detalle"] if "cuota" in d["regla"])
    assert "No registramos el pago de la cuota de septiembre 2026 ($ 10.000,00)" in d["texto"]
    assert "Según tu proyección, este año llegarías al" in d["texto"]
    assert "Cuota de septiembre 2026: $ 10.000,00; sin pago registrado." in d["dato"]


def test_cuota_parcial_informa_lo_registrado_en_el_mes(client, auth_headers):
    # Dos pagos que no llegan a la cuota: se informa la suma, no uno solo.
    _categoria(client, auth_headers, "A")
    for mes in (6, 7, 8):
        _ingreso(client, auth_headers, mes, 300_000)
    _gasto(client, auth_headers, 9, 3_000, cat="Monotributo", dia=5, desc="Pago monotributo")
    _gasto(client, auth_headers, 9, 2_000, cat="Monotributo", dia=20, desc="Pago monotributo")
    d = next(d for d in _recs(client, auth_headers)["detalle"] if "cuota" in d["regla"])
    assert "Lo registrado de la cuota de septiembre 2026 ($ 5.000,00) no cubre los $ 10.000,00" in d["texto"]
    assert "Cuota de septiembre 2026: $ 10.000,00; registrado $ 5.000,00." in d["dato"]


def test_tope_superado_sugiere_consultar_al_contador(client, auth_headers):
    _categoria(client, auth_headers, "A")
    for mes in (6, 7, 8):
        _ingreso(client, auth_headers, mes, 500_000)
    d = _recs(client, auth_headers)["detalle"][0]
    assert d["regla"].startswith("fiscal_tope_superado")
    assert "ya superó el tope de tu categoría A ($ 1.200.000,00)" in d["texto"]
    assert "Te sugerimos consultar con tu contador" in d["texto"]


def test_dashboard_recibe_la_lista_de_textos(client, auth_headers):
    escenario_muchas_senales(client, auth_headers)
    data = _recs(client, auth_headers)
    assert data["recomendaciones"] == [d["texto"] for d in data["detalle"]]
    assert all(isinstance(t, str) for t in data["recomendaciones"])


def test_sin_auth(client):
    assert client.get("/recomendaciones/").status_code == 401
