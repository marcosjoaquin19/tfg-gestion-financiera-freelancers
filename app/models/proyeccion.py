from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Proyeccion(Base):
    __tablename__ = "proyecciones"

    id = Column(Integer, primary_key=True, index=True)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    fecha_proyeccion = Column(DateTime(timezone=True), nullable=False)
    # la fecha futura que Prophet está prediciendo
    # ej: "2026-06-01" → cuánto va a ganar ese día
    
    monto_proyectado = Column(Float, nullable=False)
    # el valor que Prophet predice para esa fecha
    
    monto_lower = Column(Float, nullable=False)
    # límite inferior de la predicción (pesimista)
    # Prophet no da un número exacto sino un rango
    
    monto_upper = Column(Float, nullable=False)
    # límite superior de la predicción (optimista)
    
    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now())
    # cuando se generó esta proyección

    # Relación con usuarios
    usuario = relationship("Usuario", back_populates="proyecciones")