from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from typing import Optional
from app.models.factura import EstadoFactura


class FacturaCreate(BaseModel):
    cliente_nombre: str
    descripcion: str
    monto: float
    fecha_emision: datetime
    fecha_vencimiento: datetime

    @field_validator("monto")
    @classmethod
    def monto_debe_ser_positivo(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        return v

    @model_validator(mode="after")
    def vencimiento_debe_ser_posterior(self):
        if self.fecha_vencimiento <= self.fecha_emision:
            raise ValueError("La fecha de vencimiento debe ser posterior a la fecha de emisión")
        return self


class FacturaEstadoUpdate(BaseModel):
    estado: EstadoFactura
    fecha_pago: Optional[datetime] = None
    # fecha_pago es obligatoria solo si el nuevo estado es PAGADA
    # la validación se hace en el router


class FacturaResponse(BaseModel):
    id: int
    usuario_id: int
    cliente_nombre: str
    descripcion: str
    monto: float
    estado: EstadoFactura
    fecha_emision: datetime
    fecha_vencimiento: datetime
    fecha_pago: Optional[datetime]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
