from pydantic import BaseModel
from datetime import datetime


class ProyeccionResponse(BaseModel):
    id: int
    usuario_id: int
    fecha_proyeccion: datetime
    monto_proyectado: float
    monto_lower: float
    # límite inferior del intervalo de confianza (escenario pesimista)
    monto_upper: float
    # límite superior del intervalo de confianza (escenario optimista)
    fecha_generacion: datetime

    class Config:
        from_attributes = True


class ProyeccionGenerarRequest(BaseModel):
    periodos: int = 30
    # cuántos días hacia adelante predecir, default 30
    # Prophet genera una fila por cada día futuro
