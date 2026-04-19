"""
Pre-entrena el modelo base global con DATASET_BASE.
Ejecutar desde la raíz del proyecto:
    docker compose exec api python seed_modelo_base.py
"""
from app.database import SessionLocal
from app.services import ml_service

db = SessionLocal()
try:
    print("Entrenando modelo base con DATASET_BASE...")
    modelo = ml_service.entrenar_modelo_base(db)
    print(f"  Algoritmo:  {modelo.algoritmo}")
    print(f"  Ejemplos:   {modelo.n_ejemplos}")
    print(f"  Precisión:  {modelo.precision:.4f}" if modelo.precision else "  Precisión:  N/A")
    print("Seed completado: modelo base listo.")
finally:
    db.close()
