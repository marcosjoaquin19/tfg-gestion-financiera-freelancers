"""Carga ingresos históricos (≈19 meses extra) para el usuario demo, con
tendencia ascendente y estacionalidad (bajón de verano ene/feb). Sirve para que
las Proyecciones (Prophet) tengan una curva rica y verificable.

Idempotente: borra los ingresos marcados antes de reinsertar, así se puede
correr varias veces sin duplicar.

Uso:
    docker compose exec api python seed_historico_demo.py
"""
from datetime import datetime
from app.database import SessionLocal
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso

MARCADOR = "[hist-demo]"

# Total facturado por mes (ARS). Tendencia en alza + estacionalidad:
# picos en diciembre (cierre de año), bajones en enero/febrero (verano).
TOTALES = {
    (2024, 6): 1_450_000, (2024, 7): 1_600_000, (2024, 8): 1_520_000,
    (2024, 9): 1_780_000, (2024, 10): 1_950_000, (2024, 11): 2_100_000,
    (2024, 12): 2_500_000,
    (2025, 1): 1_650_000, (2025, 2): 1_820_000, (2025, 3): 2_250_000,
    (2025, 4): 2_150_000, (2025, 5): 2_380_000, (2025, 6): 2_520_000,
    (2025, 7): 2_650_000, (2025, 8): 2_480_000, (2025, 9): 2_720_000,
    (2025, 10): 2_850_000, (2025, 11): 3_000_000, (2025, 12): 3_350_000,
}


def main():
    db = SessionLocal()
    try:
        demo = db.query(Usuario).filter(
            Usuario.email == "demo@freelancecontrol.com"
        ).first()
        if not demo:
            print("No existe el usuario demo. Corré primero seed_demo.py")
            return

        # Limpieza idempotente de cargas previas de este script.
        borrados = db.query(Ingreso).filter(
            Ingreso.usuario_id == demo.id,
            Ingreso.descripcion.like(f"%{MARCADOR}%"),
        ).delete(synchronize_session=False)

        nuevos = []
        for (anio, mes), total in TOTALES.items():
            # Dividimos el total mensual en dos cobros (proyecto + honorarios).
            a = round(total * 0.6, 2)
            b = round(total - a, 2)
            nuevos.append(Ingreso(
                usuario_id=demo.id,
                descripcion=f"Proyecto web mensual {MARCADOR}",
                monto=a, categoria="Desarrollo Web",
                fecha=datetime(anio, mes, 8),
            ))
            nuevos.append(Ingreso(
                usuario_id=demo.id,
                descripcion=f"Honorarios consultoría {MARCADOR}",
                monto=b, categoria="Consultoría",
                fecha=datetime(anio, mes, 20),
            ))

        db.add_all(nuevos)
        db.commit()
        print(f"OK. Borrados {borrados} previos, insertados {len(nuevos)} ingresos "
              f"({len(TOTALES)} meses) para {demo.email}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
