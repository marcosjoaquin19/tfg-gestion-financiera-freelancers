"""
Modelo de datos: CategoriaMonotributo.

Representa la tabla `categorias_monotributo`: la escala oficial de AFIP con cada
categoría (A, B, C...), su límite de facturación anual y la cuota mensual. Es la
fuente de verdad que usa el módulo de monotributo para evaluar al usuario.
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean
from app.database import Base


class CategoriaMonotributo(Base):
    __tablename__ = "categorias_monotributo"

    id = Column(Integer, primary_key=True)
    letra = Column(String(2), unique=True, index=True, nullable=False)
    # letra de la categoría (ej: "A"), única
    limite_anual = Column(Numeric(15, 2), nullable=False)
    # tope de facturación anual permitido para esta categoría
    cuota_mensual = Column(Numeric(12, 2), nullable=False)
    # cuota fija mensual a pagar en esta categoría
    actividad = Column(String(20), nullable=False, default="servicios")
    # "servicios" o "venta": cada actividad tiene su propia escala de límites
    fecha_vigencia = Column(Date, nullable=False)
    # desde cuándo rige esta escala (permite versionar tablas históricas)
    activa = Column(Boolean, nullable=False, default=True)
    # solo se consideran las categorías de la escala vigente (activa=True)
