from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Ingreso(Base):
    __tablename__ = "ingresos"

    id = Column(Integer, primary_key=True, index=True)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    # ForeignKey → este campo apunta a la tabla usuarios
    # Analogía: es como una referencia cruzada entre planillas
    
    descripcion = Column(String(255), nullable=False)
    # ej: "Proyecto web para cliente X"
    
    monto = Column(Float, nullable=False)
    # el valor del ingreso en pesos/dolares
    
    categoria = Column(String(100), nullable=False)
    # ej: "Desarrollo", "Consultoría", "Diseño"
    
    fecha = Column(DateTime(timezone=True), nullable=False)
    # fecha en que se recibió el ingreso
    
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con la tabla usuarios
    # Analogía: desde un ingreso puedo acceder a los datos del usuario dueño
    usuario = relationship("Usuario", back_populates="ingresos")
     # Relaciones con otras tablas
    ingresos = relationship("Ingreso", back_populates="usuario")