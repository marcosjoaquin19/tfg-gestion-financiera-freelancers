"""
Test del seed de demostración (seed_demo.py).

En una base recién creada, la migración 0012 ya inserta la escala de febrero
2026 del monotributo como histórica (activa = false). El seed tiene que cargar
igual la escala vigente: si no, el usuario demo queda sin categoría evaluable
y la pantalla de Monotributo no muestra el semáforo.
"""

from datetime import date
from decimal import Decimal

from app.models.categoria_monotributo import CategoriaMonotributo


def test_seed_demo_carga_la_escala_vigente_aunque_exista_la_historica(db):
    # Estado de una base nueva después de `alembic upgrade head`.
    db.add(CategoriaMonotributo(
        letra="D",
        limite_anual=Decimal("26212853.42"),
        cuota_mensual=Decimal("72414.10"),
        actividad="servicios",
        fecha_vigencia=date(2026, 2, 1),
        activa=False,
    ))
    db.commit()

    from seed_demo import asegurar_categorias_monotributo
    asegurar_categorias_monotributo(db)

    vigentes = db.query(CategoriaMonotributo).filter(CategoriaMonotributo.activa.is_(True)).all()
    assert len(vigentes) == 11
    assert {c.fecha_vigencia for c in vigentes} == {date(2026, 8, 1)}
    historicas = db.query(CategoriaMonotributo).filter(CategoriaMonotributo.activa.is_(False)).count()
    assert historicas == 11
