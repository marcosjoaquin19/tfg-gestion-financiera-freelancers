"""escala de monotributo versionada por fecha de vigencia

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-27

Hasta ahora `categorias_monotributo` solo podía guardar una escala: el índice
de `letra` era ÚNICO, así que al publicarse una escala nueva la anterior se
pisaba. Consecuencia: el reporte de un mes anterior al cambio (por ejemplo,
mayo de 2026) evaluaba la cuota y el tope con valores que en ese momento no
regían, y una cuota bien pagada figuraba "sin registrar".

La tesis (riesgo R2) prevé un "catálogo de categorías del régimen versionado
en la base de datos con fecha de vigencia". Esta migración lo hace efectivo:

1. El índice de `letra` deja de ser único y la unicidad pasa a ser
   (letra, actividad, fecha_vigencia): una fila por categoría y por escala.
2. Se carga la escala vigente entre febrero y julio de 2026 (Tabla 18 de la
   tesis) como histórica (activa = false). La vigente desde el 1/8/2026
   (Tabla 19) sigue siendo la activa.
"""

from datetime import date
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDICE_LETRA = "ix_categorias_monotributo_letra"
UNICO = "uq_categoria_letra_actividad_vigencia"
VIGENCIA_FEBRERO_2026 = date(2026, 2, 1)

# Tabla 18 de la tesis: escala vigente entre febrero y julio de 2026
# (prestación de servicios). Valores con centavos según la publicación de ARCA.
ESCALA_FEBRERO_2026 = [
    ("A", "10277988.13", "42386.74"),
    ("B", "15058447.71", "48250.78"),
    ("C", "21113696.52", "56501.85"),
    ("D", "26212853.42", "72414.10"),
    ("E", "30833964.37", "102537.97"),
    ("F", "38642048.36", "129045.32"),
    ("G", "46211109.37", "197108.23"),
    ("H", "70113407.33", "447346.93"),
    ("I", "78479211.62", "824802.26"),
    ("J", "89872640.30", "999007.65"),
    ("K", "108357084.05", "1381687.90"),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("categorias_monotributo"):
        return

    indices = {i["name"]: i for i in inspector.get_indexes("categorias_monotributo")}
    if INDICE_LETRA in indices and indices[INDICE_LETRA].get("unique"):
        op.drop_index(INDICE_LETRA, table_name="categorias_monotributo")
        op.create_index(INDICE_LETRA, "categorias_monotributo", ["letra"], unique=False)

    unicos = {u["name"] for u in inspector.get_unique_constraints("categorias_monotributo")}
    if UNICO not in unicos:
        op.create_unique_constraint(UNICO, "categorias_monotributo", ["letra", "actividad", "fecha_vigencia"])

    tabla = sa.table(
        "categorias_monotributo",
        sa.column("letra", sa.String), sa.column("limite_anual", sa.Numeric),
        sa.column("cuota_mensual", sa.Numeric), sa.column("actividad", sa.String),
        sa.column("fecha_vigencia", sa.Date), sa.column("activa", sa.Boolean),
    )
    existentes = {
        fila[0] for fila in conn.execute(sa.text(
            "SELECT letra FROM categorias_monotributo "
            "WHERE actividad = 'servicios' AND fecha_vigencia = :f"
        ), {"f": VIGENCIA_FEBRERO_2026})
    }
    nuevas = [
        {"letra": letra, "limite_anual": limite, "cuota_mensual": cuota, "actividad": "servicios",
         "fecha_vigencia": VIGENCIA_FEBRERO_2026, "activa": False}
        for letra, limite, cuota in ESCALA_FEBRERO_2026 if letra not in existentes
    ]
    if nuevas:
        op.bulk_insert(tabla, nuevas)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("categorias_monotributo"):
        return
    # Volver a una sola escala: se descartan las históricas (no activas).
    conn.execute(sa.text("DELETE FROM categorias_monotributo WHERE activa = false"))
    unicos = {u["name"] for u in inspector.get_unique_constraints("categorias_monotributo")}
    if UNICO in unicos:
        op.drop_constraint(UNICO, "categorias_monotributo", type_="unique")
    op.drop_index(INDICE_LETRA, table_name="categorias_monotributo")
    op.create_index(INDICE_LETRA, "categorias_monotributo", ["letra"], unique=True)
