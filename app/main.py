"""
Punto de entrada de la API (backend) — FreelanceControl.
==========================================================

Este archivo es el "arranque" de toda la aplicación del lado del servidor.
Cuando se levanta el backend (uvicorn app.main:app), se ejecuta este módulo y
queda corriendo la API REST que el frontend (React) consume.

¿Qué hace, paso a paso?
  1. Carga las variables de entorno del archivo .env (claves, conexión a la BD).
  2. Crea las tablas en la base de datos si todavía no existen.
  3. Construye la aplicación FastAPI con su título y versión.
  4. Habilita CORS para que el frontend (localhost:3000) pueda llamar a la API.
  5. Registra (incluye) todos los "routers", es decir, cada módulo funcional
     de la app: autenticación, ingresos, gastos, facturas, etc.

Mapa de módulos de la aplicación (cada router = una sección de la app):
  - auth            → registro / login con JWT (seguridad y sesiones).
  - ingresos        → registro y consulta de ingresos del freelancer.
  - gastos          → registro de gastos (con categorización por ML).
  - facturas        → emisión y seguimiento de facturas (pendiente/pagada/vencida).
  - alertas         → auditoría: detecta registros sospechosos o inconsistentes.
  - proyecciones    → predicción de ingresos futuros (modelo Prophet).
  - resumen         → resumen financiero mensual redactado con IA (Groq).
  - recomendaciones → consejos financieros determinísticos según los datos.
  - importar        → carga masiva de movimientos desde extractos bancarios CSV.
  - monotributo     → control fiscal del monotributo argentino (categoría/límites).
  - ml              → clasificador de gastos por texto (Machine Learning local).
  - reportes        → generación de reportes (PDF / Excel).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database import engine
from app import models
from app.routers import auth, ingresos, gastos, facturas, alertas, proyecciones, resumen, recomendaciones, importar, monotributo, ml, reportes

# Carga las variables del archivo .env (ej: DATABASE_URL, SECRET_KEY, GROQ_API_KEY)
load_dotenv()

# Crea automáticamente las tablas en la base de datos a partir de los modelos
# de SQLAlchemy si aún no existen. En producción este paso lo cubren las
# migraciones de Alembic; acá sirve como red de seguridad al iniciar.
models.Base.metadata.create_all(bind=engine)

# Instancia principal de la API. El title/description/version aparecen en la
# documentación automática que FastAPI publica en /docs (Swagger UI).
app = FastAPI(
    title="Sistema de Gestión Financiera para Freelancers",
    description="API REST para gestión financiera con auditoría y predicciones",
    version="1.0.0"
)

# CORS: por seguridad, el navegador bloquea que una web llame a otra de distinto
# origen. Acá autorizamos explícitamente al frontend (React, puerto 3000/3001)
# a consumir la API. Solo se permiten esos orígenes y los métodos HTTP listados.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Registro de routers: cada uno aporta un grupo de endpoints (rutas) y queda
# montado bajo su propio prefijo (ej: /ingresos, /gastos). Este es el "índice"
# de todas las funcionalidades expuestas por la API.
app.include_router(auth.router)
app.include_router(ingresos.router)
app.include_router(gastos.router)
app.include_router(facturas.router)
app.include_router(alertas.router)
app.include_router(proyecciones.router)
app.include_router(resumen.router)
app.include_router(recomendaciones.router)
app.include_router(importar.router)
app.include_router(monotributo.router)
app.include_router(ml.router)
app.include_router(reportes.router)

# Endpoint raíz: respuesta simple para confirmar a simple vista que la API
# está levantada (útil al abrir http://localhost:8000 en el navegador).
@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente ✅"}

# Endpoint de "health check": lo usan Docker y los chequeos automáticos para
# verificar que el servicio responde antes de marcarlo como disponible.
@app.get("/health")
def health_check():
    return {"status": "ok", "servicio": "TFG Freelancers API"}