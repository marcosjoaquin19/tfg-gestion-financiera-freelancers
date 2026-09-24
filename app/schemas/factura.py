"""
Schemas (Pydantic) de Factura.

Definen y validan los datos de las facturas en la API:
  - FacturaCreate / FacturaUpdate: validan monto positivo y que el vencimiento
    sea posterior a la emisión.
  - FacturaEstadoUpdate: cambia solo el estado (y la fecha de pago).
  - FacturaResponse: JSON de salida hacia el cliente.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional
from app.models.factura import EstadoFactura


# Campos y reglas comunes a emitir y editar una factura.
class _FacturaDatos(BaseModel):
    cliente_nombre: str = Field(max_length=200)
    descripcion: str = Field(max_length=500)
    # Los topes acompañan al largo de las columnas: sin ellos, un texto más
    # largo llegaba a la base y la operación terminaba en un error 500.

    monto: float = Field(allow_inf_nan=False)
    # allow_inf_nan=False: un NaN pasaba el control de "mayor a cero" y
    # quedaba guardado en la base aunque la API respondiera con error.

    fecha_emision: datetime
    fecha_vencimiento: datetime

    @field_validator("cliente_nombre", "descripcion")
    @classmethod
    def texto_no_vacio(cls, v, info):
        v = v.strip()
        if not v:
            if info.field_name == "cliente_nombre":
                raise ValueError("El cliente no puede estar vacío")
            raise ValueError("La descripción no puede estar vacía")
        return v

    @field_validator("monto")
    @classmethod
    def monto_debe_ser_positivo(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        # La columna es Numeric(12, 2): admite hasta 10 dígitos enteros.
        if v >= 10 ** 10:
            raise ValueError("El monto supera el máximo admitido (10.000.000.000)")
        return v

    @model_validator(mode="after")
    def vencimiento_debe_ser_posterior(self):
        if self.fecha_vencimiento <= self.fecha_emision:
            raise ValueError("La fecha de vencimiento debe ser posterior a la fecha de emisión")
        return self


# Datos para emitir una factura nueva.
class FacturaCreate(_FacturaDatos):
    pass


# Datos para editar una factura existente (mismas validaciones que al crear).
class FacturaUpdate(_FacturaDatos):
    pass


class FacturaEstadoUpdate(BaseModel):
    estado: EstadoFactura
    fecha_pago: Optional[datetime] = None
    # fecha_pago es obligatoria si el nuevo estado es PAGADA (se valida en el
    # router, junto con que no sea anterior a la emisión) y no se admite en
    # los demás estados: una factura sin cobrar no tiene fecha de cobro.

    @model_validator(mode="after")
    def fecha_pago_solo_si_pagada(self):
        if self.fecha_pago is not None and self.estado != EstadoFactura.PAGADA:
            raise ValueError("La fecha de pago solo corresponde a una factura pagada")
        return self


# Estructura de la factura tal como la API la devuelve.
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
