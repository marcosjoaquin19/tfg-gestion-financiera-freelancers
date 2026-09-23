"""
Schemas (Pydantic) de Ingreso.

Validan y dan forma a los datos de ingresos en la API:
  - IngresoCreate:   valida el cuerpo del POST /ingresos.
  - IngresoResponse: JSON de salida hacia el cliente.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# -------------------------------------------------------------------
# SCHEMA DE CREACIÓN
# Body del POST /ingresos
# -------------------------------------------------------------------
class IngresoCreate(BaseModel):
    descripcion: str = Field(min_length=1, max_length=255)
    # ej: "Proyecto web para cliente X"
    # Los topes acompañan al largo de la columna `descripcion` (String(255)).
    # Sin ellos, un texto más largo pasaba la validación, llegaba al INSERT y
    # la base cortaba la operación con un error 500 sin explicación.

    monto: float
    # el valor del ingreso, debe ser positivo y caber en Numeric(12, 2)

    categoria: str = Field(min_length=1, max_length=100)
    # ej: "Desarrollo", "Consultoría", "Diseño"
    # Mismo criterio que la descripción: la columna admite 100 caracteres.

    fecha: datetime
    # fecha en que se recibió el ingreso
    # el cliente manda un string ISO 8601 y Pydantic lo convierte automáticamente
    # ej: "2026-03-08T14:00:00"

    @field_validator("monto")
    @classmethod
    def monto_debe_ser_positivo(cls, v):
        # validación custom → un ingreso no puede ser negativo ni cero
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        # La columna es Numeric(12, 2): admite hasta 10 dígitos enteros.
        # Un importe mayor no entra en la base, así que se rechaza acá con un
        # mensaje entendible en lugar de dejar que falle el INSERT.
        if v >= 10 ** 10:
            raise ValueError("El monto supera el máximo admitido (10.000.000.000)")
        return v


# -------------------------------------------------------------------
# SCHEMA DE RESPUESTA
# Lo que devuelve la API al crear o consultar un ingreso
# -------------------------------------------------------------------
class IngresoResponse(BaseModel):
    id: int
    usuario_id: int
    descripcion: str
    monto: float
    categoria: str
    fecha: datetime
    fecha_creacion: datetime
    # fecha_creacion la genera PostgreSQL automáticamente, por eso no está en Create

    class Config:
        from_attributes = True
        # permite leer desde objetos SQLAlchemy además de diccionarios
