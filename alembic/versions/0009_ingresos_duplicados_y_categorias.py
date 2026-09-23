"""detección de ingresos duplicados y categorías normalizadas

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-22

Dos cambios sobre la tabla `ingresos`, ambos motivados por el mismo riesgo:
un ingreso cargado dos veces infla la facturación de los últimos 12 meses y
puede hacer que el semáforo del Monotributo anuncie un cambio de categoría
que no corresponde.

1. Columna `es_duplicado`. Equivalente a la que ya tiene `gastos`. El router
   la marca al crear un ingreso cuando detecta otro idéntico el mismo día.
   Es una advertencia visible, no un bloqueo: dos cobros iguales el mismo día
   son posibles y el usuario decide.

2. Normalización de categorías históricas. A partir de ahora la API valida la
   categoría contra una lista cerrada (CATEGORIAS_INGRESO). Los ingresos ya
   cargados con etiquetas de versiones anteriores del prototipo quedarían
   inconsistentes con esa lista, así que se reescriben a su equivalente. Sin
   este paso, editar uno de esos registros devolvería un error de validación.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.services.categorias_ingreso import CATEGORIAS_INGRESO, EQUIVALENCIAS_HISTORICAS


revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columnas = {c["name"] for c in inspector.get_columns("ingresos")}
    if "es_duplicado" not in columnas:
        # server_default para que las filas existentes queden en False y la
        # columna pueda ser NOT NULL; se retira después para que el valor lo
        # fije la aplicación, igual que en `gastos`.
        op.add_column(
            "ingresos",
            sa.Column("es_duplicado", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.alter_column("ingresos", "es_duplicado", server_default=None)

    # Categorías de versiones anteriores → equivalente de la lista vigente.
    for historica, vigente in EQUIVALENCIAS_HISTORICAS.items():
        conn.execute(
            sa.text("UPDATE ingresos SET categoria = :vigente WHERE categoria = :historica"),
            {"vigente": vigente, "historica": historica},
        )

    # Cualquier otra etiqueta fuera de la lista pasa a "Otros": es preferible
    # un rubro genérico a un registro que la API ya no acepta editar.
    conn.execute(
        sa.text("UPDATE ingresos SET categoria = 'Otros' WHERE categoria NOT IN :validas").bindparams(
            sa.bindparam("validas", value=tuple(CATEGORIAS_INGRESO), expanding=True)
        )
    )


def downgrade() -> None:
    # Las categorías reescritas no se revierten: el mapeo es de muchos a uno y
    # no hay forma de saber cuál era la etiqueta original de cada fila.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columnas = {c["name"] for c in inspector.get_columns("ingresos")}
    if "es_duplicado" in columnas:
        op.drop_column("ingresos", "es_duplicado")
