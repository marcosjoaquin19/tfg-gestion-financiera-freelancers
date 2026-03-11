from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Carga las variables del .env
load_dotenv()

# Lee la URL de conexión a PostgreSQL desde el .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Crea el "motor" de conexión a la base de datos
# Analogía: es como abrir un canal entre Python y PostgreSQL
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# Crea una "fábrica" de sesiones
# Analogía: cada sesión es una conversación individual con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para todos los modelos (tablas)
# Analogía: es el molde del que van a heredar todas tus tablas
Base = declarative_base()

# Función que abre y cierra la conexión automáticamente
# Analogía: es como un mozo que toma el pedido y cuando termina cierra la comanda
def get_db():
    db = SessionLocal()
    try:
        yield db        # entrega la conexión al endpoint que la necesite
    finally:
        db.close()      # siempre cierra la conexión al terminar