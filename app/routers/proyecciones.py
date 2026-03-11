from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.proyeccion import Proyeccion
from app.models.ingreso import Ingreso
from app.schemas.proyeccion import ProyeccionResponse, ProyeccionGenerarRequest
from app.dependencies import get_current_user
import pandas as pd
from prophet import Prophet


router = APIRouter(prefix="/proyecciones", tags=["Proyecciones"])

MIN_INGRESOS_PARA_PROYECTAR = 10
# Prophet necesita suficientes datos históricos para hacer predicciones confiables
# con menos de 10 registros los resultados no son significativos


@router.post("/generar", response_model=list[ProyeccionResponse], status_code=status.HTTP_201_CREATED)
def generar_proyecciones(
    datos: ProyeccionGenerarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # 1. Obtener el historial de ingresos del usuario
    ingresos = db.query(Ingreso).filter(
        Ingreso.usuario_id == current_user.id
    ).order_by(Ingreso.fecha.asc()).all()

    if len(ingresos) < MIN_INGRESOS_PARA_PROYECTAR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se necesitan al menos {MIN_INGRESOS_PARA_PROYECTAR} ingresos registrados para generar proyecciones",
        )

    # 2. Armar el DataFrame que espera Prophet
    # Prophet requiere exactamente dos columnas: "ds" (fecha) e "y" (valor)
    df = pd.DataFrame([
        {"ds": ingreso.fecha, "y": ingreso.monto}
        for ingreso in ingresos
    ])
    df["ds"] = pd.to_datetime(df["ds"]).dt.tz_localize(None)
    # Prophet no acepta fechas con timezone → las removemos

    # 3. Entrenar el modelo y predecir
    modelo = Prophet()
    modelo.fit(df)

    futuro = modelo.make_future_dataframe(periods=datos.periodos)
    # make_future_dataframe genera las fechas futuras a predecir

    forecast = modelo.predict(futuro)
    # forecast devuelve un DataFrame con columnas: ds, yhat, yhat_lower, yhat_upper
    # yhat → predicción central, yhat_lower/upper → intervalo de confianza

    # 4. Tomar solo las filas futuras (las últimas `periodos` filas)
    predicciones_futuras = forecast.tail(datos.periodos)

    # 5. Eliminar proyecciones anteriores del usuario antes de guardar las nuevas
    # así siempre tiene el set más reciente, no acumulamos filas viejas
    db.query(Proyeccion).filter(Proyeccion.usuario_id == current_user.id).delete()

    # 6. Guardar las nuevas proyecciones en la BD
    nuevas_proyecciones = []
    for _, fila in predicciones_futuras.iterrows():
        proyeccion = Proyeccion(
            usuario_id=current_user.id,
            fecha_proyeccion=fila["ds"].to_pydatetime(),
            monto_proyectado=max(fila["yhat"], 0),
            # max(..., 0) → Prophet puede predecir valores negativos, lo corregimos
            monto_lower=max(fila["yhat_lower"], 0),
            monto_upper=max(fila["yhat_upper"], 0),
        )
        db.add(proyeccion)
        nuevas_proyecciones.append(proyeccion)

    db.commit()
    for p in nuevas_proyecciones:
        db.refresh(p)

    return nuevas_proyecciones


@router.get("/", response_model=list[ProyeccionResponse])
def listar_proyecciones(
    limite: int = Query(default=30, ge=1, le=365),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    proyecciones = db.query(Proyeccion).filter(
        Proyeccion.usuario_id == current_user.id
    ).order_by(Proyeccion.fecha_proyeccion.asc()).offset(offset).limit(limite).all()

    return proyecciones


@router.get("/{proyeccion_id}", response_model=ProyeccionResponse)
def obtener_proyeccion(
    proyeccion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    proyeccion = db.query(Proyeccion).filter(
        Proyeccion.id == proyeccion_id,
        Proyeccion.usuario_id == current_user.id,
    ).first()

    if not proyeccion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyección no encontrada")

    return proyeccion
