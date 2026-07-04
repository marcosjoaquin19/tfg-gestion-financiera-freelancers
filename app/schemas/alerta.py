"""
Schemas (Pydantic) de Alerta de auditoría.

  - AlertaResponse:        JSON de salida de cada alerta detectada por el módulo
    de auditoría (duplicados, montos atípicos, etc.).
  - AlertaResolverUpdate:  cuerpo para marcar una alerta como resuelta o reabrirla.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.alerta_auditoria import TipoAlerta


# Estructura de una alerta tal como la API la devuelve.
class AlertaResponse(BaseModel):
    id: int
    usuario_id: int
    tipo: TipoAlerta
    descripcion: str
    monto_involucrado: Optional[float]
    gasto_id_duplicado: Optional[int] = None
    # solo en alertas de gasto duplicado: id del gasto repetido referenciado
    resuelta: bool
    fecha_deteccion: datetime

    class Config:
        from_attributes = True


class AlertaResolverUpdate(BaseModel):
    resuelta: bool
    # permite marcar como resuelta (True) o reabrir (False) una alerta
