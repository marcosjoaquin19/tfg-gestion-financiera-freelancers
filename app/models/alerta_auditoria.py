from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# Tipos de alertas que puede detectar el módulo M3
class TipoAlerta(enum.Enum):
    GASTO_DUPLICADO = "gasto_duplicado"
    # detectó dos gastos iguales en fechas cercanas
    
    ANOMALIA_ESTADISTICA = "anomalia_estadistica"
    # un gasto es muy alto comparado al promedio
    
    DISCREPANCIA_FACTURACION = "discrepancia_facturacion"
    # hay facturas emitidas pero no hay ingresos que las justifiquen

    RIESGO_RECATEGORIZACION = "riesgo_recategorizacion"
    FACTURA_IMPAGA = "factura_impaga"
    COMISION_EXCESIVA = "comision_excesiva"

class AlertaAuditoria(Base):
    __tablename__ = "alertas_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    
    tipo = Column(Enum(TipoAlerta), nullable=False)
    # qué tipo de alerta es
    
    descripcion = Column(String(500), nullable=False)
    # explicación en texto de qué se detectó
    # ej: "Gasto duplicado: $5000 en Adobe el 01/03 y 02/03"
    
    monto_involucrado = Column(Numeric(12, 2), nullable=True)
    # el monto relacionado a la alerta (puede ser null)
    
    resuelta = Column(Boolean, default=False)
    # False → alerta activa, el usuario no la revisó
    # True → el usuario la marcó como revisada
    
    fecha_deteccion = Column(DateTime(timezone=True), server_default=func.now())
    # cuando el sistema detectó la anomalía

    # Relación con usuarios
    usuario = relationship("Usuario", back_populates="alertas_auditoria")