"""método de cálculo en cada proyección

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-27

Agrega la columna `metodo` a `proyecciones` para que la pantalla declare si la
proyección se calculó con Prophet o con la media móvil del arranque en frío
(o si solo había ingresos del mes en curso, o ninguno). Las filas previas
quedan en NULL: se reemplazan en la siguiente generación.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("proyecciones"):
        return
    columnas = {c["name"] for c in inspector.get_columns("proyecciones")}
    if "metodo" not in columnas:
        op.add_column("proyecciones", sa.Column("metodo", sa.String(20), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("proyecciones"):
        return
    columnas = {c["name"] for c in inspector.get_columns("proyecciones")}
    if "metodo" in columnas:
        op.drop_column("proyecciones", "metodo")
