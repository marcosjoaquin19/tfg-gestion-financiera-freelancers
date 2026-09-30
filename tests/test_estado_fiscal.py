"""
Tests del estado fiscal del Monotributo (GET /monotributo/estado, HU-10).

Acumulado real del año + proyección hasta diciembre contra el tope de la
categoría. El reloj se fija con el fixture `hoy` (por defecto 27-sep-2026) y
los escenarios usan pocos ingresos para que la proyección sea el arranque en
frío (promedio de los últimos 3 meses cerrados): así los montos esperados se
pueden calcular a mano.
"""

from datetime import datetime
from decimal import Decimal

import pytest

import app.services.prophet_service as ps
import app.services.monotributo_service as ms

# Escala de prueba: (letra, tope anual, cuota mensual)
ESCALA = [
    ("A", "1200000", "10000"),
    ("B", "1800000", "12000"),
    ("C", "2400000", "14000"),
    ("D", "3000000", "16000"),
    ("E", "4500000", "20000"),
    ("K", "6000000", "50000"),
]


@pytest.fixture(autouse=True)
def escala(client):
    from datetime import date
    from app.database import get_db
    from app.main import app
    from app.models.categoria_monotributo import CategoriaMonotributo

    db = next(app.dependency_overrides[get_db]())
    for letra, limite, cuota in ESCALA:
        db.add(CategoriaMonotributo(
            letra=letra, limite_anual=Decimal(limite), cuota_mensual=Decimal(cuota),
            actividad="servicios", fecha_vigencia=date(2026, 8, 1), activa=True,
        ))
    db.commit()


@pytest.fixture
def hoy(monkeypatch):
    """Fija el reloj de proyecciones y monotributo. Devuelve un setter."""
    def fijar(dia: datetime):
        class Fija(datetime):
            @classmethod
            def now(cls, tz=None):
                return dia.replace(tzinfo=tz) if tz else dia
        monkeypatch.setattr(ps, "datetime", Fija)
    fijar(datetime(2026, 9, 27, 12))
    return fijar


def _categoria(client, headers, letra="A"):
    r = client.patch("/monotributo/categoria", json={"categoria_monotributo": letra}, headers=headers)
    assert r.status_code == 200, r.text


def _ingreso(client, headers, anio, mes, monto, dia=10):
    r = client.post("/ingresos/", json={
        "descripcion": "Honorarios", "monto": monto, "categoria": "Servicios",
        "fecha": f"{anio}-{mes:02d}-{dia:02d}T12:00:00",
    }, headers=headers)
    assert r.status_code == 201, r.text


def _estado(client, headers):
    r = client.get("/monotributo/estado", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# --- Límite ya superado, categoría sugerida y exclusión -----------------------

def test_limite_ya_superado_no_se_informa_como_sin_riesgo(client, auth_headers, hoy):
    # Regresión: con lo facturado por encima del tope, meses_para_limite venía
    # vacío y la pantalla lo mostraba como "✓ Sin riesgo este año".
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 7, 700_000)
    _ingreso(client, auth_headers, 2026, 8, 700_000)

    e = _estado(client, auth_headers)
    assert e["facturado_anual"] == 1_400_000
    assert e["limite_superado"] is True
    assert e["meses_para_limite"] == 0
    assert e["estado"] == "rojo"


def test_sugiere_la_categoria_que_cubre_la_proyeccion(client, auth_headers, hoy):
    # Regresión: sugería siempre la letra siguiente (B, tope $1,8M) aunque la
    # proyección ($4,2M) también la superara.
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 7, 700_000)
    _ingreso(client, auth_headers, 2026, 8, 700_000)

    e = _estado(client, auth_headers)
    # 1,4M facturado + 0,7M (septiembre) + 3 × 0,7M (oct-dic)
    assert e["proyeccion_anual"] == 4_200_000
    assert e["categoria_siguiente"] == "B"
    assert e["categoria_sugerida"] == "E"
    assert e["excede_regimen"] is False


def test_supera_la_categoria_mas_alta(client, auth_headers, hoy):
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 7, 2_000_000)
    _ingreso(client, auth_headers, 2026, 8, 2_000_000)

    e = _estado(client, auth_headers)
    assert e["proyeccion_anual"] == 12_000_000
    assert e["categoria_sugerida"] is None
    assert e["excede_regimen"] is True


def test_sin_sugerencia_si_la_proyeccion_no_supera_el_tope(client, auth_headers, hoy):
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 50_000)
    e = _estado(client, auth_headers)
    assert e["estado"] == "verde"
    assert e["categoria_sugerida"] is None and e["excede_regimen"] is False


# --- Proyección siempre al día --------------------------------------------------

def test_proyeccion_se_genera_sola_si_no_existe(client, auth_headers, hoy):
    # Regresión: si el usuario nunca abrió Proyecciones, el semáforo usaba
    # solo lo facturado.
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 100_000)

    e = _estado(client, auth_headers)
    assert e["proyeccion_anual"] == 500_000     # 100k + 100k (sep) + 3 × 100k
    assert len(client.get("/proyecciones/", headers=auth_headers).json()) == 6


def test_proyeccion_se_regenera_si_cambian_los_ingresos(client, auth_headers, hoy):
    # Regresión: después de importar un extracto, el semáforo seguía con la
    # proyección vieja hasta que el usuario la regeneraba a mano.
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 100_000)
    assert _estado(client, auth_headers)["proyeccion_anual"] == 500_000

    _ingreso(client, auth_headers, 2026, 8, 200_000, dia=20)   # agosto pasa a 300k
    assert _estado(client, auth_headers)["proyeccion_anual"] == 1_500_000


def test_proyeccion_se_regenera_si_se_borra_un_ingreso(client, auth_headers, hoy):
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 100_000)
    _ingreso(client, auth_headers, 2026, 8, 200_000, dia=20)
    assert _estado(client, auth_headers)["proyeccion_anual"] == 1_500_000

    ultimo = client.get("/ingresos/", headers=auth_headers).json()[0]
    assert client.delete(f"/ingresos/{ultimo['id']}", headers=auth_headers).status_code == 204
    assert _estado(client, auth_headers)["proyeccion_anual"] in (500_000, 1_000_000)


def test_no_regenera_si_nada_cambio(client, auth_headers, hoy):
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 100_000)
    _estado(client, auth_headers)
    ids = [p["id"] for p in client.get("/proyecciones/", headers=auth_headers).json()]
    _estado(client, auth_headers)
    assert [p["id"] for p in client.get("/proyecciones/", headers=auth_headers).json()] == ids


def test_regenera_al_empezar_un_mes_nuevo(client, auth_headers, hoy):
    # Al cambiar de mes cambian los meses cerrados: la proyección vieja ya
    # no corresponde aunque los ingresos sean los mismos.
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 100_000)
    _estado(client, auth_headers)
    antes = client.get("/proyecciones/", headers=auth_headers).json()

    hoy(datetime(2026, 10, 2, 12))
    _estado(client, auth_headers)
    despues = client.get("/proyecciones/", headers=auth_headers).json()
    assert despues[0]["fecha_proyeccion"][:7] == "2026-11"
    assert antes[0]["fecha_proyeccion"][:7] == "2026-10"


def test_si_prophet_falla_el_estado_se_calcula_igual(client, auth_headers, hoy, monkeypatch):
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 100_000)

    def falla(*args, **kwargs):
        raise RuntimeError("Prophet no disponible")
    monkeypatch.setattr(ms, "asegurar_proyecciones_vigentes", falla)

    e = _estado(client, auth_headers)
    assert e["facturado_anual"] == 100_000
    assert e["proyeccion_anual"] == 100_000     # sin proyección guardada: solo lo real


# --- Qué cuenta como facturado ---------------------------------------------------

def test_fecha_futura_no_es_facturacion(client, auth_headers, hoy):
    # Regresión: un cobro cargado con fecha 20-dic sumaba como facturado real.
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 8, 100_000)
    _ingreso(client, auth_headers, 2026, 12, 900_000, dia=20)
    assert _estado(client, auth_headers)["facturado_anual"] == 100_000


def test_ingresos_del_anio_anterior_no_cuentan(client, auth_headers, hoy):
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2025, 12, 900_000)
    _ingreso(client, auth_headers, 2026, 1, 100_000)
    assert _estado(client, auth_headers)["facturado_anual"] == 100_000


def test_facturacion_12_meses_excluye_fechas_futuras(client, auth_headers):
    _ingreso(client, auth_headers, 2030, 1, 900_000)
    assert client.get("/monotributo/facturacion-12-meses", headers=auth_headers).json()["facturacion_12_meses"] == 0


@pytest.fixture
def instante(monkeypatch):
    """Fija el reloj en un instante real (UTC): a diferencia de `hoy`, la
    hora de Argentina y la de UTC quedan tres horas corridas, como en el
    servidor."""
    from datetime import timezone

    def fijar(momento_utc: datetime):
        momento = momento_utc.replace(tzinfo=timezone.utc)

        class Reloj(datetime):
            @classmethod
            def now(cls, tz=None):
                return momento.astimezone(tz) if tz else momento.replace(tzinfo=None)
        monkeypatch.setattr(ps, "datetime", Reloj)
    return fijar


def _ingreso_del_dia(client, headers, fecha, monto):
    # Como lo manda la pantalla: solo el día, sin hora.
    r = client.post("/ingresos/", json={
        "descripcion": "Honorarios", "monto": monto, "categoria": "Servicios", "fecha": fecha,
    }, headers=headers)
    assert r.status_code == 201, r.text


def test_cobro_de_manana_a_las_22_no_es_facturacion(client, auth_headers, instante):
    # 31/10 a las 22 h de Argentina ya es 1/11 en UTC. Regresión: el cobro
    # fechado el 1/11 sumaba como facturado real y la ventana de 12 meses
    # terminaba "mañana".
    instante(datetime(2026, 11, 1, 1, 0))
    _categoria(client, auth_headers, "A")
    _ingreso_del_dia(client, auth_headers, "2026-10-31", 100_000)
    _ingreso_del_dia(client, auth_headers, "2026-11-01", 500_000)
    assert _estado(client, auth_headers)["facturado_anual"] == 100_000
    f12 = client.get("/monotributo/facturacion-12-meses", headers=auth_headers).json()
    assert f12["facturacion_12_meses"] == 100_000
    assert (f12["desde"], f12["hasta"]) == ("2025-11-01", "2026-10-31")


def test_31_de_diciembre_a_la_noche_el_cobro_del_1_de_enero_no_suma_al_anio(client, auth_headers, instante):
    instante(datetime(2027, 1, 1, 1, 0))          # 31/12/2026 22 h en Argentina
    _categoria(client, auth_headers, "A")
    _ingreso_del_dia(client, auth_headers, "2026-12-10", 100_000)
    _ingreso_del_dia(client, auth_headers, "2027-01-01", 700_000)
    assert _estado(client, auth_headers)["facturado_anual"] == 100_000


def test_el_cobro_de_hoy_cuenta_aunque_sea_temprano(client, auth_headers, instante):
    instante(datetime(2026, 10, 14, 3, 30))       # 14/10 00:30 en Argentina
    _categoria(client, auth_headers, "A")
    _ingreso_del_dia(client, auth_headers, "2026-10-14", 100_000)
    assert _estado(client, auth_headers)["facturado_anual"] == 100_000
    f12 = client.get("/monotributo/facturacion-12-meses", headers=auth_headers).json()
    assert f12["facturacion_12_meses"] == 100_000
    assert f12["hasta"] == "2026-10-14"


# --- Mes en curso y meses hasta diciembre -----------------------------------------

def test_mes_en_curso_suma_lo_esperado_si_todavia_se_cobro_menos(client, auth_headers, hoy):
    # Regresión: el resto del mes en curso no se proyectaba y la estimación
    # anual perdía un mes entero.
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 7, 300_000)
    _ingreso(client, auth_headers, 2026, 8, 300_000)
    _ingreso(client, auth_headers, 2026, 9, 100_000, dia=3)
    e = _estado(client, auth_headers)
    assert e["facturado_anual"] == 700_000
    assert e["proyeccion_anual"] == 1_800_000   # 600k + sep 300k + 3 × 300k


def test_mes_en_curso_cuenta_lo_cobrado_si_supera_lo_esperado(client, auth_headers, hoy):
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 7, 300_000)
    _ingreso(client, auth_headers, 2026, 8, 300_000)
    _ingreso(client, auth_headers, 2026, 9, 500_000, dia=3)
    assert _estado(client, auth_headers)["proyeccion_anual"] == 2_000_000   # 1,1M + 3 × 300k


def test_primer_semestre_completa_hasta_diciembre(client, auth_headers, hoy):
    # En febrero, la proyección de 6 meses llega a agosto: septiembre a
    # diciembre se completan con el promedio proyectado.
    hoy(datetime(2026, 2, 15, 12))
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 1, 50_000)
    e = _estado(client, auth_headers)
    assert e["meses_estimados_con_promedio"] == 4
    assert e["proyeccion_anual"] == 600_000     # ene 50k + feb 50k + 10 × 50k


def test_diciembre_solo_suma_el_mes_en_curso(client, auth_headers, hoy):
    hoy(datetime(2026, 12, 10, 12))
    _categoria(client, auth_headers, "A")
    _ingreso(client, auth_headers, 2026, 11, 100_000)
    e = _estado(client, auth_headers)
    assert e["meses_estimados_con_promedio"] == 0
    assert e["proyeccion_anual"] == 200_000     # nov 100k + dic 100k


# --- Mes en que se cruza el tope --------------------------------------------------

def test_informa_el_mes_en_que_se_cruza_el_tope(client, auth_headers, hoy):
    _categoria(client, auth_headers, "A")          # tope 1,2M
    for mes in (6, 7, 8):
        _ingreso(client, auth_headers, 2026, mes, 200_000)
    e = _estado(client, auth_headers)
    # 600k → sep 800k → oct 1,0M → nov 1,2M (no lo supera) → dic 1,4M
    assert e["mes_limite"] == "Diciembre 2026"
    assert e["meses_para_limite"] == 3


def test_sin_mes_si_no_se_cruza_antes_de_diciembre(client, auth_headers, hoy):
    # Regresión: informaba "4,4 meses" aunque eso cayera en el año siguiente,
    # y la pantalla lo mostraba en rojo con el semáforo en amarillo.
    _categoria(client, auth_headers, "A")
    for mes in (6, 7, 8):
        _ingreso(client, auth_headers, 2026, mes, 150_000)
    e = _estado(client, auth_headers)
    assert e["proyeccion_anual"] == 1_050_000      # 87,5 % del tope
    assert e["estado"] == "amarillo"
    assert e["meses_para_limite"] is None and e["mes_limite"] is None
    assert e["limite_superado"] is False


# --- Bordes del semáforo (HU-10) --------------------------------------------------

@pytest.mark.parametrize("mensual, meses, esperado", [
    (120_000, (6, 7, 8), "amarillo"),            # 840k  → 70 % exacto
    (120_000, (4, 5, 6, 7, 8), "amarillo"),      # 1,08M → 90 % exacto
    (100_000, (6, 7, 8), "verde"),               # 700k  → 58,3 %
    (140_000, (4, 5, 6, 7, 8), "rojo"),          # 1,26M → 105 %
])
def test_bordes_del_semaforo(client, auth_headers, hoy, mensual, meses, esperado):
    # Rojo es "por encima del 90 %": el 90 % exacto es amarillo, y el 70 %
    # exacto ya es amarillo.
    _categoria(client, auth_headers, "A")
    for mes in meses:
        _ingreso(client, auth_headers, 2026, mes, mensual)
    assert _estado(client, auth_headers)["estado"] == esperado
