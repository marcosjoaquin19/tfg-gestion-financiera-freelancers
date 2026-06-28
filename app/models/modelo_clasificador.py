"""
Modelo de datos: ModeloClasificador.

Representa la tabla `modelos_clasificador`: guarda cada modelo de Machine
Learning entrenado para clasificar gastos por su descripción. El modelo entrenado
se serializa y se almacena en la BD para poder reutilizarlo sin reentrenar.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ModeloClasificador(Base):
    __tablename__ = "modelos_clasificador"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    # dueño del modelo; null = modelo base compartido por todos los usuarios
    modelo_serializado = Column(Text, nullable=False)
    # el modelo entrenado (pipeline sklearn) serializado en texto base64
    algoritmo = Column(String(20), nullable=False)
    # algoritmo usado: "naive_bayes" o "svm"
    precision = Column(Float, nullable=True)
    # precisión estimada del modelo (validación cruzada) al entrenarlo
    n_ejemplos = Column(Integer, default=0)
    # cantidad de ejemplos con los que se entrenó
    fecha_entrenamiento = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    # solo un modelo por usuario queda activo a la vez (el último entrenado)
