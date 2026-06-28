"""
Schemas (Pydantic) de Proyeccion.

  - ProyeccionResponse:        JSON de salida de cada punto proyectado por Prophet.
  - ProyeccionGenerarRequest:  cuerpo del POST que indica cuántos períodos predecir.
"""

from pydantic import BaseModel
from datetime import datetime


# Estructura de un punto de proyección tal como la API lo devuelve.
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
    periodos: int = 6
    # cuántos meses hacia adelante predecir, default 6 (alineado con HU-09:
    # "proyección de ingresos para los próximos seis meses").
    # Prophet se invoca con freq="MS" (Month Start), así que cada fila del
    # forecast corresponde al primer día de un mes futuro.
