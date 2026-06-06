"""
Inserta (o actualiza) las 11 categorías de monotributo (PRESTACIÓN DE SERVICIOS)
vigentes desde junio 2026. Ejecutar desde la raíz del proyecto:
    python seed_categorias_monotributo.py

Fuente: escala publicada para junio 2026 (cruzada entre Ámbito y Estudio Brady,
valores idénticos en ambas). NOTA: son datos impositivos que ARCA actualiza
periódicamente → verificar contra arca.gob.ar antes de usar en producción/defensa.

También exporta seed_categorias(db) para reutilizar desde otros seeds
(p. ej. seed_demo.py) sin ejecutar nada al importar el módulo.
"""
from datetime import date
from app.database import SessionLocal
from app.models.categoria_monotributo import CategoriaMonotributo

CATEGORIAS = [
    {"letra": "A", "limite_anual": 10277988.13,  "cuota_mensual": 42386.74},
    {"letra": "B", "limite_anual": 15058447.71,  "cuota_mensual": 48250.78},
    {"letra": "C", "limite_anual": 21113696.52,  "cuota_mensual": 56501.85},
    {"letra": "D", "limite_anual": 26212853.42,  "cuota_mensual": 72414.10},
    {"letra": "E", "limite_anual": 30833964.37,  "cuota_mensual": 102537.97},
    {"letra": "F", "limite_anual": 38642048.36,  "cuota_mensual": 129045.32},
    {"letra": "G", "limite_anual": 46211109.37,  "cuota_mensual": 197108.23},
    {"letra": "H", "limite_anual": 70113407.33,  "cuota_mensual": 447346.93},
    {"letra": "I", "limite_anual": 78479211.62,  "cuota_mensual": 824802.26},
    {"letra": "J", "limite_anual": 89872640.30,  "cuota_mensual": 999007.65},
    {"letra": "K", "limite_anual": 108357084.05, "cuota_mensual": 1381687.90},
]

FECHA_VIGENCIA = date(2026, 6, 1)


def seed_categorias(db=None):
    """Inserta o actualiza las 11 categorías. Idempotente.

    Si no se pasa una sesión, abre y cierra una propia. Si se pasa (desde otro
    seed que ya tiene sesión abierta), opera sobre ella y NO la cierra.
    """
    propia = db is None
    if propia:
        db = SessionLocal()
    try:
        insertadas = actualizadas = 0
        for datos in CATEGORIAS:
            existente = db.query(CategoriaMonotributo).filter(
                CategoriaMonotributo.letra == datos["letra"]
            ).first()
            if existente:
                existente.limite_anual = datos["limite_anual"]
                existente.cuota_mensual = datos["cuota_mensual"]
                existente.fecha_vigencia = FECHA_VIGENCIA
                existente.activa = True
                actualizadas += 1
            else:
                db.add(CategoriaMonotributo(
                    letra=datos["letra"],
                    limite_anual=datos["limite_anual"],
                    cuota_mensual=datos["cuota_mensual"],
                    actividad="servicios",
                    fecha_vigencia=FECHA_VIGENCIA,
                    activa=True,
                ))
                insertadas += 1
        db.commit()
        print(f"Categorías Monotributo: {insertadas} insertadas, {actualizadas} actualizadas.")
    finally:
        if propia:
            db.close()


if __name__ == "__main__":
    seed_categorias()
