from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.alerta_auditoria import TipoAlerta


class AlertaResponse(BaseModel):
    id: int
    usuario_id: int
    tipo: TipoAlerta
    descripcion: str
    monto_involucrado: Optional[float]
    resuelta: bool
    fecha_deteccion: datetime

    class Config:
        from_attributes = True


class AlertaResolverUpdate(BaseModel):
    resuelta: bool
    # permite marcar como resuelta (True) o reabrir (False) una alerta
