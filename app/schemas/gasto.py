from pydantic import BaseModel, field_validator
from datetime import datetime


class GastoCreate(BaseModel):
    descripcion: str
    monto: float
    categoria: str
    fecha: datetime

    @field_validator("monto")
    @classmethod
    def monto_debe_ser_positivo(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        return v


class GastoResponse(BaseModel):
    id: int
    usuario_id: int
    descripcion: str
    monto: float
    categoria: str
    fecha: datetime
    es_duplicado: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True
