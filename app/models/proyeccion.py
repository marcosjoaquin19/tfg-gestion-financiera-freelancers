"""
Modelo de datos: Proyeccion.

Representa la tabla `proyecciones`. Cada fila es un punto de la predicción de
ingresos generada por el modelo Prophet: una fecha futura con su monto estimado
y el rango (inferior/superior) del intervalo de confianza.
"""

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Proyeccion(Base):
    __tablename__ = "proyecciones"

    id = Column(Integer, primary_key=True, index=True)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)

    fecha_proyeccion = Column(DateTime(timezone=True), nullable=False, index=True)
    # la fecha futura que Prophet está prediciendo
    # ej: "2026-06-01" → cuánto va a ganar ese día
    
    monto_proyectado = Column(Numeric(12, 2), nullable=False)
    # el valor que Prophet predice para esa fecha

    monto_lower = Column(Numeric(12, 2), nullable=False)
    # límite inferior de la predicción (pesimista)
    # Prophet no da un número exacto sino un rango

    monto_upper = Column(Numeric(12, 2), nullable=False)
    # límite superior de la predicción (optimista)
    
    metodo = Column(String(20), nullable=True)
    # con qué se calculó: "prophet", "media_movil" (pocos datos), "mes_en_curso"
    # (solo hay ingresos del mes que todavía no terminó) o "sin_datos".
    # Se guarda para que la pantalla lo declare. NULL en filas anteriores a la
    # migración 0010.

    firma = Column(String(40), nullable=True)
    # huella de los ingresos con los que se calculó (ver
    # prophet_service.firma_ingresos): si no coincide con la actual, la
    # proyección quedó vieja y el estado fiscal la regenera. Migración 0011.

    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now())
    # cuando se generó esta proyección

    # Relación con usuarios
    usuario = relationship("Usuario", back_populates="proyecciones")