"""
Modelo de datos: Ingreso.

Representa la tabla `ingresos`. Cada fila es un cobro registrado por el
freelancer (monto, categoría y fecha), asociado al usuario dueño.
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Ingreso(Base):
    __tablename__ = "ingresos"

    id = Column(Integer, primary_key=True, index=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # ForeignKey → vincula el ingreso con su usuario en la tabla usuarios

    descripcion = Column(String(255), nullable=False)
    # ej: "Proyecto web para cliente X"
    
    monto = Column(Numeric(12, 2), nullable=False)
    # el valor del ingreso en pesos/dolares
    
    categoria = Column(String(100), nullable=False)
    # ej: "Desarrollo", "Consultoría", "Diseño"
    
    fecha = Column(DateTime(timezone=True), nullable=False)
    # fecha en que se recibió el ingreso
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relación inversa: permite acceder al usuario dueño desde un ingreso.
    usuario = relationship("Usuario", back_populates="ingresos")