from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean
from app.database import Base


class CategoriaMonotributo(Base):
    __tablename__ = "categorias_monotributo"

    id = Column(Integer, primary_key=True)
    letra = Column(String(2), unique=True, index=True, nullable=False)
    limite_anual = Column(Numeric(15, 2), nullable=False)
    cuota_mensual = Column(Numeric(12, 2), nullable=False)
    actividad = Column(String(20), nullable=False, default="servicios")
    fecha_vigencia = Column(Date, nullable=False)
    activa = Column(Boolean, nullable=False, default=True)
