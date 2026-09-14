"""
Configuración de la conexión a la base de datos (PostgreSQL).

Centraliza la creación del motor de conexión, la fábrica de sesiones y la clase
Base de la que heredan todos los modelos. El resto de la app obtiene una sesión
de base de datos llamando a get_db().
"""

# PATRÓN: Factory — sessionmaker() fabrica sesiones bajo demanda.
# PATRÓN: Singleton — un único engine con pool de conexiones para todo el proceso.
# PATRÓN: Unit of Work — cada Session agrupa operaciones y confirma o revierte en bloque.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Carga las variables del .env
load_dotenv()

# Lee la URL de conexión a PostgreSQL desde el .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Motor de conexión a la base de datos. El pool reutiliza hasta 5 conexiones
# abiertas (más 10 extra bajo demanda) para no abrir una nueva por cada request.
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# Fábrica de sesiones: cada sesión representa una unidad de trabajo con la BD.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredan todos los modelos (tablas) de la aplicación.
Base = declarative_base()

# Dependencia de FastAPI: entrega una sesión de BD al endpoint y la cierra
# automáticamente al terminar, aunque ocurra un error.
def get_db():
    db = SessionLocal()
    try:
        yield db        # entrega la conexión al endpoint que la necesite
    finally:
        db.close()      # siempre cierra la conexión al terminar