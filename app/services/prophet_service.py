"""
Servicio de Proyecciones — predicción de ingresos con Prophet.

Usa la librería Prophet (modelo de series temporales de Meta) para predecir los
ingresos futuros del freelancer a partir de su historial. Devuelve, por período,
el monto estimado y el rango (inferior/superior) del intervalo de confianza.
Con pocos datos no usa Prophet: recurre a una media móvil (arranque en frío).
Solo se entrena con meses cerrados y siempre se proyecta desde el mes que viene.
"""

# PATRÓN: Strategy + Degradación elegante — Prophet si hay historial suficiente, media móvil si no.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib
import logging
import statistics
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
import cmdstanpy  # noqa: F401 — debe importarse antes que Prophet para que use CMDSTANPY
from prophet import Prophet
from app.models.ingreso import Ingreso
from app.models.proyeccion import Proyeccion

logger = logging.getLogger(__name__)

MIN_INGRESOS_PROPHET = 10
# por debajo de este umbral Prophet no tiene suficientes datos → usamos media móvil

MIN_MESES_PROPHET = 3
# Prophet ajusta una tendencia sobre los totales mensuales. Con dos meses la
# "tendencia" es la recta que pasa por dos puntos: encaja perfecto sin importar
# los datos y se extrapola sin ningún control (1M y 3M → 13M en seis meses).
# Con tres o más meses ya hay algo que ajustar.

HORIZONTE_MAX_MESES = 6
# HU-09: proyección de los próximos seis meses. Más allá, en series cortas e
# irregulares como las de un freelancer, el error pasa a dominar la estimación.

VENTANA_MEDIA_MOVIL = 3
# el arranque en frío promedia los últimos 3 meses cerrados

# Método con el que se calculó cada proyección (se guarda y se muestra).
METODO_PROPHET = "prophet"
METODO_MEDIA_MOVIL = "media_movil"
METODO_MES_EN_CURSO = "mes_en_curso"
# solo hay ingresos del mes que todavía no terminó: estimación provisoria
METODO_SIN_DATOS = "sin_datos"


def ahora_utc() -> datetime:
    """Reloj único de proyecciones y monotributo (UTC, como las fechas guardadas)."""
    return datetime.now(timezone.utc)


ZONA_AR = ZoneInfo("America/Argentina/Buenos_Aires")


def inicio_mes_en_curso() -> datetime:
    """Primer día del mes en curso según el calendario de Argentina, sin zona.

    Las fechas se cargan como día calendario (guardado a las 00:00 UTC), así
    que el mes que las agrupa es el del calendario local. Con el reloj en UTC,
    desde las 21 h del último día del mes el sistema ya creía estar en el mes
    siguiente: la cuota recién pagada figuraba impaga y el resumen por
    defecto era de un mes vacío.
    """
    ahora = datetime.now(ZONA_AR)
    return datetime(ahora.year, ahora.month, 1)


def firma_ingresos(ingresos) -> str:
    """Huella de los datos de los que depende la proyección.

    Cambia si se agrega, borra o edita un ingreso (id, monto o mes) y también
    cuando empieza un mes nuevo, porque cambian los meses cerrados. Así se
    detecta una proyección vieja sin comparar resultados.
    """
    h = hashlib.sha1(inicio_mes_en_curso().strftime("%Y-%m").encode())
    for ingreso in sorted(ingresos, key=lambda i: i.id):
        h.update(f"|{ingreso.id}:{float(ingreso.monto):.2f}:{ingreso.fecha.year}-{ingreso.fecha.month}".encode())
    return h.hexdigest()


def _clave_mes(fecha: datetime) -> datetime:
    return datetime(fecha.year, fecha.month, 1)


def serie_mensual(ingresos) -> tuple[list[tuple[datetime, float]], float, int]:
    """Totales por mes con los que se entrena, más el parcial del mes en curso.

    Devuelve (serie, total_mes_en_curso, ingresos_en_meses_cerrados).

    - Solo entran los meses CERRADOS: el mes en curso todavía no terminó y,
      tratado como un mes completo, parece una caída brusca que Prophet
      extrapola hacia cero. Tampoco entran fechas futuras.
    - Los meses sin ingresos que quedan ENTRE el primero y el último con datos
      cuentan como $0: para un freelancer, un mes sin cobrar es un dato real.
      No se completa con ceros después del último mes con datos, porque eso
      puede ser un extracto que todavía no se importó.
    """
    mes_actual = inicio_mes_en_curso()
    totales: dict[datetime, float] = {}
    total_en_curso = 0.0
    cantidad_cerrados = 0

    for ingreso in ingresos:
        mes = _clave_mes(ingreso.fecha)
        if mes < mes_actual:
            totales[mes] = totales.get(mes, 0.0) + float(ingreso.monto)
            cantidad_cerrados += 1
        elif mes == mes_actual:
            total_en_curso += float(ingreso.monto)

    if not totales:
        return [], round(total_en_curso, 2), 0

    serie = []
    mes = min(totales)
    ultimo = max(totales)
    while mes <= ultimo:
        serie.append((mes, round(totales.get(mes, 0.0), 2)))
        mes += relativedelta(months=1)

    return serie, round(total_en_curso, 2), cantidad_cerrados


def _proyeccion(usuario_id, mes, yhat, lower, upper, metodo) -> Proyeccion:
    return Proyeccion(
        usuario_id=usuario_id,
        fecha_proyeccion=mes.replace(tzinfo=timezone.utc),
        monto_proyectado=round(max(yhat, 0), 2),
        monto_lower=round(max(lower, 0), 2),
        monto_upper=round(max(upper, 0), 2),
        metodo=metodo,
    )


def _meses_a_proyectar(periodos: int) -> list[datetime]:
    """Siempre desde el mes que viene, aunque el último dato sea viejo: una
    proyección nunca cae sobre un mes que ya pasó."""
    primero = inicio_mes_en_curso() + relativedelta(months=1)
    return [primero + relativedelta(months=k) for k in range(periodos)]


def _proyecciones_media_movil(usuario_id: int, montos: list[float], periodos: int, metodo: str) -> list[Proyeccion]:
    """
    Cold start: pocos datos para Prophet.
    Proyecta el promedio de los montos mensuales recibidos para cada mes futuro.
    El rango lower/upper usa ±1 desviación estándar (o ±20% si hay menos de 2 datos).
    """
    media = sum(montos) / len(montos) if montos else 0.0
    desviacion = statistics.stdev(montos) if len(montos) >= 2 else media * 0.2

    return [
        _proyeccion(usuario_id, mes, media, media - desviacion, media + desviacion, metodo)
        for mes in _meses_a_proyectar(periodos)
    ]


def _proyecciones_prophet(usuario_id: int, serie, periodos: int) -> list[Proyeccion]:
    df = pd.DataFrame(serie, columns=["ds", "y"])

    meses = _meses_a_proyectar(periodos)
    ultimo_dato = df["ds"].max()
    # Prophet predice a partir del mes siguiente al último dato. Si ese dato es
    # viejo, hay que pedirle también los meses intermedios y descartarlos.
    faltan = relativedelta(meses[-1], ultimo_dato)
    pasos = faltan.years * 12 + faltan.months

    modelo = Prophet(stan_backend="CMDSTANPY")
    modelo.fit(df)
    # freq="MS" → Month Start: cada predicción es el primer día de cada mes
    futuro = modelo.make_future_dataframe(periods=pasos, freq="MS", include_history=False)
    # Prophet calcula el intervalo de confianza (lower/upper) con simulación
    # Monte Carlo. Fijamos la semilla para que el resultado sea REPRODUCIBLE:
    # misma data → misma proyección, incluida la banda. Clave para defender el modelo.
    np.random.seed(42)
    forecast = modelo.predict(futuro)
    forecast = forecast[forecast["ds"] >= meses[0]].head(periodos)

    return [
        _proyeccion(usuario_id, fila["ds"].to_pydatetime(), fila["yhat"],
                    fila["yhat_lower"], fila["yhat_upper"], METODO_PROPHET)
        for _, fila in forecast.iterrows()
    ]


def generar_proyecciones(db: Session, usuario_id: int, periodos: int = HORIZONTE_MAX_MESES) -> list[Proyeccion]:
    ingresos = (
        db.query(Ingreso)
        .filter(Ingreso.usuario_id == usuario_id)
        .order_by(Ingreso.fecha.asc())
        .all()
    )

    serie, total_en_curso, cantidad_cerrados = serie_mensual(ingresos)
    montos = [total for _, total in serie]

    if cantidad_cerrados >= MIN_INGRESOS_PROPHET and len(serie) >= MIN_MESES_PROPHET:
        try:
            nuevas = _proyecciones_prophet(usuario_id, serie, periodos)
        except Exception:
            # Si Prophet falla (por ejemplo, el optimizador no converge), la
            # pantalla no se cae: se proyecta con la media móvil, la misma
            # estrategia del arranque en frío, y el método guardado lo dice.
            logger.exception("Prophet falló para el usuario %s; se usa la media móvil", usuario_id)
            nuevas = _proyecciones_media_movil(
                usuario_id, montos[-VENTANA_MEDIA_MOVIL:], periodos, METODO_MEDIA_MOVIL,
            )
    elif serie:
        nuevas = _proyecciones_media_movil(
            usuario_id, montos[-VENTANA_MEDIA_MOVIL:], periodos, METODO_MEDIA_MOVIL,
        )
    elif total_en_curso > 0:
        # Usuario nuevo con ingresos solo en el mes que todavía no terminó:
        # es un piso, no un promedio, y se informa como estimación provisoria.
        nuevas = _proyecciones_media_movil(usuario_id, [total_en_curso], periodos, METODO_MES_EN_CURSO)
    else:
        nuevas = _proyecciones_media_movil(usuario_id, [], periodos, METODO_SIN_DATOS)

    firma = firma_ingresos(ingresos)
    for p in nuevas:
        p.firma = firma

    db.query(Proyeccion).filter(Proyeccion.usuario_id == usuario_id).delete()
    db.add_all(nuevas)
    db.commit()
    for p in nuevas:
        db.refresh(p)

    return nuevas


def asegurar_proyecciones_vigentes(db: Session, usuario_id: int) -> list[Proyeccion]:
    """Devuelve las proyecciones guardadas si siguen correspondiendo a los
    ingresos actuales; si no existen o quedaron viejas, las regenera.

    La usa el estado fiscal: sin esto, el semáforo sumaba una proyección
    calculada antes de la última importación (o ninguna, si el usuario nunca
    abrió Proyecciones).
    """
    actuales = db.query(Proyeccion).filter(Proyeccion.usuario_id == usuario_id).all()
    ingresos = db.query(Ingreso).filter(Ingreso.usuario_id == usuario_id).all()
    firma = firma_ingresos(ingresos)
    if actuales and all(p.firma == firma for p in actuales):
        return actuales
    return generar_proyecciones(db, usuario_id)
