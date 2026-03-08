from fastapi import FastAPI
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

# Crea la aplicación FastAPI
# Analogía: es como abrir las puertas de tu negocio
app = FastAPI(
    title="Sistema de Gestión Financiera para Freelancers",
    description="API REST para gestión financiera con auditoría y predicciones",
    version="1.0.0"
)

# Ruta de prueba - el "hola mundo" de tu API
# Analogía: es como el cartel de "estamos abiertos"
@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente ✅"}

# Ruta para verificar que el servidor está vivo
@app.get("/health")
def health_check():
    return {"status": "ok", "servicio": "TFG Freelancers API"}


from fastapi import FastAPI
from dotenv import load_dotenv
from app.database import engine
from app import models

# Carga las variables del .env
load_dotenv()

# Crea todas las tablas en PostgreSQL automáticamente
# Analogía: es como ejecutar "CREATE TABLE" en SQL pero automático
models.Base.metadata.create_all(bind=engine)

# Crea la aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión Financiera para Freelancers",
    description="API REST para gestión financiera con auditoría y predicciones",
    version="1.0.0"
)

# Ruta de prueba
@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente ✅"}

# Ruta para verificar que el servidor está vivo
@app.get("/health")
def health_check():
    return {"status": "ok", "servicio": "TFG Freelancers API"}