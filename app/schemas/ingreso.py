from pydantic import BaseModel, field_validator
from datetime import datetime


# -------------------------------------------------------------------
# SCHEMA DE CREACIÓN
# Body del POST /ingresos
# -------------------------------------------------------------------
class IngresoCreate(BaseModel):
    descripcion: str
    # ej: "Proyecto web para cliente X"

    monto: float
    # el valor del ingreso, debe ser positivo

    categoria: str
    # ej: "Desarrollo", "Consultoría", "Diseño"

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
