from datetime import datetime, timezone, timedelta
import statistics
from sqlalchemy.orm import Session
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
    Proyecta la media de los ingresos disponibles para cada día futuro.
    El rango lower/upper usa ±1 desviación estándar (o ±20% si hay menos de 2 datos).
    """
    montos = [float(i.monto) for i in ingresos]
    media = sum(montos) / len(montos) if montos else 0.0
    desviacion = statistics.stdev(montos) if len(montos) >= 2 else media * 0.2

    hoy = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return [
        Proyeccion(
            usuario_id=usuario_id,
            fecha_proyeccion=hoy + timedelta(days=dia),
            monto_proyectado=round(media, 2),
            monto_lower=round(max(media - desviacion, 0), 2),
            monto_upper=round(media + desviacion, 2),
        )
        for dia in range(1, periodos + 1)
    ]


def _proyecciones_prophet(usuario_id: int, ingresos, periodos: int) -> list[Proyeccion]:
    df = pd.DataFrame([
        {"ds": ingreso.fecha, "y": float(ingreso.monto)}
        for ingreso in ingresos
    ])
    df["ds"] = pd.to_datetime(df["ds"]).dt.tz_localize(None)
    # Prophet no acepta fechas con timezone → las removemos

    modelo = Prophet(stan_backend="CMDSTANPY")
    modelo.fit(df)
    futuro = modelo.make_future_dataframe(periods=periodos)
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


def generar_proyecciones(db: Session, usuario_id: int, periodos: int = 90) -> list[Proyeccion]:
    ingresos = (
        db.query(Ingreso)
        .filter(Ingreso.usuario_id == usuario_id)
        .order_by(Ingreso.fecha.asc())
        .all()
    )

    if len(ingresos) < MIN_INGRESOS_PROPHET:
        nuevas = _proyecciones_media_movil(usuario_id, ingresos, periodos)
    else:
        nuevas = _proyecciones_prophet(usuario_id, ingresos, periodos)

    db.query(Proyeccion).filter(Proyeccion.usuario_id == usuario_id).delete()
    db.add_all(nuevas)
    db.commit()
    for p in nuevas:
        db.refresh(p)

    return nuevas
