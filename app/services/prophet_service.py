"""
Servicio de Proyecciones — predicción de ingresos con Prophet.

Usa la librería Prophet (modelo de series temporales de Meta) para predecir los
ingresos futuros del freelancer a partir de su historial. Devuelve, por período,
el monto estimado y el rango (inferior/superior) del intervalo de confianza.
Requiere un mínimo de ingresos históricos para entrenar; si no, no proyecta.
"""

from datetime import datetime, timezone
import statistics
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
import cmdstanpy  # noqa: F401 — debe importarse antes que Prophet para que use CMDSTANPY
from prophet import Prophet
from app.models.ingreso import Ingreso
from app.models.proyeccion import Proyeccion

MIN_INGRESOS_PROPHET = 10
# por debajo de este umbral Prophet no tiene suficientes datos → usamos media móvil


def _proyecciones_media_movil(usuario_id: int, ingresos, periodos: int) -> list[Proyeccion]:
    """
    Cold start: menos de MIN_INGRESOS_PROPHET registros.
    Proyecta la media de los ingresos disponibles para cada mes futuro.
    El rango lower/upper usa ±1 desviación estándar (o ±20% si hay menos de 2 datos).
    periodos = número de meses a proyectar.
    """
    montos = [float(i.monto) for i in ingresos]
    media = sum(montos) / len(montos) if montos else 0.0
    desviacion = statistics.stdev(montos) if len(montos) >= 2 else media * 0.2

    # Primer día del mes siguiente como punto de partida
    primer_mes_siguiente = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ) + relativedelta(months=1)

    return [
        Proyeccion(
            usuario_id=usuario_id,
            fecha_proyeccion=primer_mes_siguiente + relativedelta(months=mes),
            monto_proyectado=round(media, 2),
            monto_lower=round(max(media - desviacion, 0), 2),
            monto_upper=round(media + desviacion, 2),
        )
        for mes in range(periodos)
    ]


def _proyecciones_prophet(usuario_id: int, ingresos, periodos: int) -> list[Proyeccion]:
    df = pd.DataFrame([
        {"ds": ingreso.fecha, "y": float(ingreso.monto)}
        for ingreso in ingresos
    ])
    df["ds"] = pd.to_datetime(df["ds"]).dt.tz_localize(None)
    # Prophet no acepta fechas con timezone → las removemos

    # Agrupar por mes: sumamos todos los ingresos de cada mes en un único punto.
    # Esto evita el ruido diario y produce proyecciones mensuales más estables.
    df["ds"] = df["ds"].dt.to_period("M").dt.to_timestamp()
    df = df.groupby("ds")["y"].sum().reset_index()

    modelo = Prophet(stan_backend="CMDSTANPY")
    modelo.fit(df)
    # freq="MS" → Month Start: cada predicción es el primer día de cada mes
    futuro = modelo.make_future_dataframe(periods=periodos, freq="MS")
    # Prophet calcula el intervalo de confianza (lower/upper) con simulación
    # Monte Carlo. Fijamos la semilla para que el resultado sea REPRODUCIBLE:
    # misma data → misma proyección, incluida la banda. Clave para defender el modelo.
    np.random.seed(42)
    forecast = modelo.predict(futuro)

    return [
        Proyeccion(
            usuario_id=usuario_id,
            fecha_proyeccion=fila["ds"].to_pydatetime(),
            monto_proyectado=round(max(fila["yhat"], 0), 2),
            monto_lower=round(max(fila["yhat_lower"], 0), 2),
            monto_upper=round(max(fila["yhat_upper"], 0), 2),
        )
        for _, fila in forecast.tail(periodos).iterrows()
    ]


def generar_proyecciones(db: Session, usuario_id: int, periodos: int = 6) -> list[Proyeccion]:
    ingresos = (
        db.query(Ingreso)
        .filter(Ingreso.usuario_id == usuario_id)
        .order_by(Ingreso.fecha.asc())
        .all()
    )

    # Prophet ajusta una tendencia sobre los totales MENSUALES, así que además
    # del mínimo de registros necesita al menos dos meses distintos de
    # historial: con todo concentrado en un solo mes el DataFrame agrupado
    # queda con una única fila y el fit de Prophet falla. En ese caso (usuario
    # nuevo que cargó muchos movimientos juntos) usamos la media móvil.
    meses_distintos = {(i.fecha.year, i.fecha.month) for i in ingresos}

    if len(ingresos) < MIN_INGRESOS_PROPHET or len(meses_distintos) < 2:
        nuevas = _proyecciones_media_movil(usuario_id, ingresos, periodos)
    else:
        nuevas = _proyecciones_prophet(usuario_id, ingresos, periodos)

    db.query(Proyeccion).filter(Proyeccion.usuario_id == usuario_id).delete()
    db.add_all(nuevas)
    db.commit()
    for p in nuevas:
        db.refresh(p)

    return nuevas
