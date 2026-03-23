from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database import engine
from app import models
from app.routers import auth, ingresos, gastos, facturas, alertas, proyecciones, resumen, recomendaciones, importar, monotributo

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión Financiera para Freelancers",
    description="API REST para gestión financiera con auditoría y predicciones",
    version="1.0.0"
)

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

@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente ✅"}

@app.get("/health")
def health_check():
    return {"status": "ok", "servicio": "TFG Freelancers API"}