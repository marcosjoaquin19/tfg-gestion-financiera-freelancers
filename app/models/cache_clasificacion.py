from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class CacheClasificacion(Base):
    __tablename__ = "cache_clasificacion"

    id = Column(Integer, primary_key=True, index=True)
    descripcion_normalizada = Column(String, unique=True, index=True, nullable=False)
    categoria = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
