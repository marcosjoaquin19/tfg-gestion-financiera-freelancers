"""
Modelo de datos: CacheClasificacion.

Representa la tabla `cache_clasificacion`. Guarda las correcciones manuales que
el usuario hace sobre la categoría de un gasto en el playground del clasificador.
Esas correcciones se usan como ejemplos extra al reentrenar el modelo personal.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.sql import func
from app.database import Base


class CacheClasificacion(Base):
    """Correcciones explícitas que el usuario aporta desde el playground del
    clasificador (POST /ml/corregir). Cada fila es un ejemplo de entrenamiento
    extra que se suma a los gastos reales del usuario al ejecutar el
    reentrenamiento del modelo personalizado.

    Históricamente esta tabla fue caché de respuestas del clasificador externo
    (Groq); con la migración al clasificador NLP local cambió de rol pero se
    conservó el nombre por compatibilidad con el historial de migraciones.
    """

    __tablename__ = "cache_clasificacion"

    id = Column(Integer, primary_key=True, index=True)

    usuario_id = Column(
        Integer, ForeignKey("usuarios.id"), nullable=True, index=True,
    )
    # nullable para tolerar filas del rol anterior (caché global de Groq).
    # Las correcciones nuevas siempre se persisten con usuario_id poblado.

    descripcion_normalizada = Column(String, index=True, nullable=False)
    categoria = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        # Una corrección por (usuario, descripción): si el usuario vuelve a
        # corregir la misma descripción, se sobreescribe la categoría.
        UniqueConstraint(
            "usuario_id", "descripcion_normalizada",
            name="uq_cache_usuario_desc",
        ),
    )
