from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# Definimos los estados posibles de una factura
# Analogía: es como los estados de un pedido de delivery
# "preparando" → "en camino" → "entregado"
class EstadoFactura(enum.Enum):
    PENDIENTE = "pendiente"     # emitida pero no cobrada
    PAGADA = "pagada"           # cobrada exitosamente
    VENCIDA = "vencida"         # no se cobró y venció el plazo

class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    cliente_nombre = Column(String(200), nullable=False)
    # nombre del cliente al que le facturamos
    
    descripcion = Column(String(500), nullable=False)
    # detalle del servicio facturado
    
    monto = Column(Numeric(12, 2), nullable=False)
    # monto de la factura
    
    estado = Column(Enum(EstadoFactura), default=EstadoFactura.PENDIENTE)
    # estado actual de la factura
    
    fecha_emision = Column(DateTime(timezone=True), nullable=False)
    # cuando se emitió la factura
    
    fecha_vencimiento = Column(DateTime(timezone=True), nullable=False)
    # cuando vence el plazo de pago
    
    fecha_pago = Column(DateTime(timezone=True), nullable=True)
    # cuando se cobró (puede ser null si todavía no se pagó)
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con usuarios
    usuario = relationship("Usuario", back_populates="facturas")