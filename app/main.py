from fastapi import FastAPI
from dotenv import load_dotenv
from app.database import engine
from app import models
from app.routers import auth, ingresos, gastos, facturas, alertas, proyecciones, resumen

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión Financiera para Freelancers",
    description="API REST para gestión financiera con auditoría y predicciones",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(ingresos.router)
app.include_router(gastos.router)
app.include_router(facturas.router)
app.include_router(alertas.router)
app.include_router(proyecciones.router)
app.include_router(resumen.router)

@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente ✅"}

@app.get("/health")
def health_check():
    return {"status": "ok", "servicio": "TFG Freelancers API"}