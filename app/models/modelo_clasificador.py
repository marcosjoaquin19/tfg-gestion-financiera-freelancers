from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ModeloClasificador(Base):
    __tablename__ = "modelos_clasificador"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    modelo_serializado = Column(Text, nullable=False)
    algoritmo = Column(String(20), nullable=False)
    precision = Column(Float, nullable=True)
    n_ejemplos = Column(Integer, default=0)
    fecha_entrenamiento = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
