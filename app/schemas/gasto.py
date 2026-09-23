"""
Schemas (Pydantic) de Gasto.

Definen la forma de los datos que entran y salen de la API para los gastos:
  - GastoCreate:   valida el cuerpo del request al crear un gasto.
  - GastoResponse: define el JSON que la API devuelve al cliente.
Validar acá evita que datos inválidos (ej: monto negativo) lleguen a la BD.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from app.services.categorias_gasto import CATEGORIAS_GASTO


# Datos que el cliente debe enviar para registrar un gasto.
class GastoCreate(BaseModel):
    descripcion: str = Field(max_length=255)
    # El tope acompaña al largo de la columna (String(255)): sin él, un texto
    # más largo llegaba al INSERT y la base cortaba con un error 500.

    monto: float = Field(allow_inf_nan=False)
    # allow_inf_nan=False: el formato JSON que acepta Python admite NaN e
    # Infinity. Sin esto, un NaN pasaba los controles (NaN no es "<= 0") y se
    # guardaba en la base, rompiendo cualquier suma posterior.

    # Opcional a propósito (HU-04): el usuario puede registrar un gasto con solo
    # descripción y monto, y el clasificador local infiere la categoría. La
    # interfaz igual la envía, porque muestra la sugerencia para que el usuario
    # la confirme o la modifique antes de guardar.
    categoria: str | None = None
    fecha: datetime

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v):
        # Un gasto sin descripción no se puede identificar en el listado ni
        # clasificar: el modelo no tiene ninguna palabra de la cual aprender.
        v = v.strip()
        if not v:
            raise ValueError("La descripción no puede estar vacía")
        return v

    # Regla de negocio: no se aceptan gastos con monto cero o negativo.
    @field_validator("monto")
    @classmethod
    def monto_debe_ser_positivo(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        # La columna es Numeric(12, 2): admite hasta 10 dígitos enteros.
        if v >= 10 ** 10:
            raise ValueError("El monto supera el máximo admitido (10.000.000.000)")
        return v

    @field_validator("categoria")
    @classmethod
    def categoria_debe_estar_en_la_lista(cls, v):
        # La pantalla ofrece un desplegable, pero la API se puede llamar
        # directamente. Una categoría fuera de la lista no solo fragmenta los
        # totales: entra al reentrenamiento como una clase nueva que el
        # clasificador después empieza a sugerir.
        if v is not None and v not in CATEGORIAS_GASTO:
            raise ValueError(
                "Categoría inválida. Las válidas son: " + ", ".join(CATEGORIAS_GASTO)
            )
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
