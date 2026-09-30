"""
Schemas (Pydantic) de Proyeccion.

  - ProyeccionResponse:        JSON de salida de cada punto proyectado por Prophet.
  - ProyeccionGenerarRequest:  cuerpo del POST que indica cuántos períodos predecir.
"""

from pydantic import BaseModel, Field
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
    metodo: str | None = None
    # "prophet", "media_movil", "respaldo", "mes_en_curso" o "sin_datos" (ver prophet_service)
    fecha_generacion: datetime

    class Config:
        from_attributes = True


class ProyeccionGenerarRequest(BaseModel):
    periodos: int = Field(default=6, ge=1, le=6)
    # cuántos meses hacia adelante predecir, default 6 (alineado con HU-09:
    # "proyección de ingresos para los próximos seis meses").
    # Prophet se invoca con freq="MS" (Month Start), así que cada fila del
    # forecast corresponde al primer día de un mes futuro.
    # Acotado a 1..6: con 0 se borraba la proyección sin guardar nada, y con
    # un número negativo se guardaban meses ya pasados como si fueran futuros.


class MesHistorico(BaseModel):
    mes: datetime
    total: float


class HistoricoResponse(BaseModel):
    # La serie exacta con la que se entrena: meses cerrados, con los huecos
    # intermedios en $0. El gráfico dibuja esto, no una suma aparte.
    meses: list[MesHistorico]
    mes_en_curso: datetime
    total_mes_en_curso: float
    # lo cobrado en el mes que todavía no terminó (no entra en el cálculo)
