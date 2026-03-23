"""
Inserta (o actualiza) las 11 categorías de monotributo vigentes desde 2026-02-01.
Ejecutar desde la raíz del proyecto:
    python seed_categorias_monotributo.py
"""
from datetime import date
from app.database import SessionLocal
from app.models.categoria_monotributo import CategoriaMonotributo

CATEGORIAS = [
    {"letra": "A", "limite_anual": 10277988,  "cuota_mensual": 42387},
    {"letra": "B", "limite_anual": 15068988,  "cuota_mensual": 48251},
    {"letra": "C", "limite_anual": 21010988,  "cuota_mensual": 56502},
    {"letra": "D", "limite_anual": 27540988,  "cuota_mensual": 72414},
    {"letra": "E", "limite_anual": 34650988,  "cuota_mensual": 102548},
    {"letra": "F", "limite_anual": 45280988,  "cuota_mensual": 129045},
    {"letra": "G", "limite_anual": 56510988,  "cuota_mensual": 174378},
    {"letra": "H", "limite_anual": 79130988,  "cuota_mensual": 447347},
    {"letra": "I", "limite_anual": 94500988,  "cuota_mensual": 606019},
    {"letra": "J", "limite_anual": 101430988, "cuota_mensual": 805938},
    {"letra": "K", "limite_anual": 108357084, "cuota_mensual": 1080000},
]

FECHA_VIGENCIA = date(2026, 2, 1)

db = SessionLocal()
try:
    for datos in CATEGORIAS:
        existente = db.query(CategoriaMonotributo).filter(
            CategoriaMonotributo.letra == datos["letra"]
        ).first()
        if existente:
            existente.limite_anual = datos["limite_anual"]
            existente.cuota_mensual = datos["cuota_mensual"]
            existente.fecha_vigencia = FECHA_VIGENCIA
            existente.activa = True
            print(f"  Actualizada categoría {datos['letra']}")
        else:
            db.add(CategoriaMonotributo(
                letra=datos["letra"],
                limite_anual=datos["limite_anual"],
                cuota_mensual=datos["cuota_mensual"],
                actividad="servicios",
                fecha_vigencia=FECHA_VIGENCIA,
                activa=True,
            ))
            print(f"  Insertada categoría {datos['letra']}")
    db.commit()
    print("Seed completado: 11 categorías cargadas.")
finally:
    db.close()
