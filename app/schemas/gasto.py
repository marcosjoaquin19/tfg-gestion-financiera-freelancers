"""
Schemas (Pydantic) de Gasto.

Definen la forma de los datos que entran y salen de la API para los gastos:
  - GastoCreate:   valida el cuerpo del request al crear un gasto.
  - GastoResponse: define el JSON que la API devuelve al cliente.
Validar acá evita que datos inválidos (ej: monto negativo) lleguen a la BD.
"""

from pydantic import BaseModel, field_validator
from datetime import datetime


# Datos que el cliente debe enviar para registrar un gasto.
class GastoCreate(BaseModel):
    descripcion: str
    monto: float
    categoria: str
    fecha: datetime

    # Regla de negocio: no se aceptan gastos con monto cero o negativo.

    @field_validator("monto")
    @classmethod
    def monto_debe_ser_positivo(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        return v


# Estructura del gasto tal como la API lo devuelve (incluye campos calculados
# por el servidor: id, es_duplicado, fecha_creacion).
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
