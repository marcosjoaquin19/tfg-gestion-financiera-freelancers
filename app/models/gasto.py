"""
Modelo de datos: Gasto.

Representa la tabla `gastos`. Cada fila es un gasto del freelancer, con su
categoría (que puede asignarse automáticamente con el clasificador de ML) y un
flag que el módulo de auditoría usa para marcar posibles duplicados.
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # FK → este gasto pertenece a un usuario
    
    descripcion = Column(String(255), nullable=False)
    # ej: "Suscripción Adobe", "Hosting servidor"
    
    monto = Column(Numeric(12, 2), nullable=False)
    # el valor del gasto
    
    categoria = Column(String(100), nullable=False)
    # ej: "Software", "Infraestructura", "Marketing"
    
    fecha = Column(DateTime(timezone=True), nullable=False)
    # fecha en que se realizó el gasto
    
    es_duplicado = Column(Boolean, default=False)
    # el módulo de auditoría M3 va a marcar esto como True
    # si detecta que es un gasto duplicado
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con usuarios
    usuario = relationship("Usuario", back_populates="gastos")