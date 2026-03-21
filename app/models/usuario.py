from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship

class Usuario(Base):
    # Nombre de la tabla en PostgreSQL
    __tablename__ = "usuarios"

    # Columnas de la tabla
    # Analogía: cada Column es una columna de una planilla Excel
    id = Column(Integer, primary_key=True, index=True)
    # primary_key=True → es el identificador único de cada fila
    
    nombre = Column(String(100), nullable=False)
    # nullable=False → este campo es obligatorio, no puede estar vacío
    
    email = Column(String(150), unique=True, nullable=False, index=True)
    # unique=True → no puede haber dos usuarios con el mismo email
    
    password_hash = Column(String(255), nullable=False)
    # guardamos el password encriptado, nunca el password real
    
    es_activo = Column(Boolean, default=True)

    categoria_monotributo = Column(String(2), nullable=True)
    actividad_monotributo = Column(String(20), default="servicios")
    # si el usuario está activo o fue desactivado
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    # se llena automáticamente con la fecha y hora actual

    ingresos = relationship("Ingreso", back_populates="usuario")
    gastos = relationship("Gasto", back_populates="usuario")
    facturas = relationship("Factura", back_populates="usuario")
    proyecciones = relationship("Proyeccion", back_populates="usuario")
    alertas_auditoria = relationship("AlertaAuditoria", back_populates="usuario")
    