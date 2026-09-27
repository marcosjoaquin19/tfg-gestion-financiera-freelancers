"""
Modelo de datos: CategoriaMonotributo.

Representa la tabla `categorias_monotributo`: la escala oficial de AFIP con cada
categoría (A, B, C...), su límite de facturación anual y la cuota mensual. Es la
fuente de verdad que usa el módulo de monotributo para evaluar al usuario.
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, UniqueConstraint
from app.database import Base


class CategoriaMonotributo(Base):
    __tablename__ = "categorias_monotributo"

    id = Column(Integer, primary_key=True)
    __table_args__ = (
        # Una fila por categoría y por escala (migración 0012): el catálogo
        # guarda cada escala publicada con su fecha de vigencia, y la vigente
        # es la marcada como activa. Así un reporte de un mes anterior se
        # evalúa con la escala que regía en ese mes.
        UniqueConstraint("letra", "actividad", "fecha_vigencia", name="uq_categoria_letra_actividad_vigencia"),
    )

    letra = Column(String(2), index=True, nullable=False)
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
