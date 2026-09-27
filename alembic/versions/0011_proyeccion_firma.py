"""huella de los ingresos en cada proyección

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-27

Agrega la columna `firma` a `proyecciones`: una huella de los ingresos con los
que se calculó. El estado fiscal del Monotributo la compara con la de los
ingresos actuales y, si no coincide (se importó un extracto, se borró un
ingreso, empezó un mes nuevo), regenera la proyección antes de usarla. Las
filas previas quedan en NULL y se regeneran en la primera consulta.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("proyecciones"):
        return
    columnas = {c["name"] for c in inspector.get_columns("proyecciones")}
    if "firma" not in columnas:
        op.add_column("proyecciones", sa.Column("firma", sa.String(40), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("proyecciones"):
        return
    columnas = {c["name"] for c in inspector.get_columns("proyecciones")}
    if "firma" in columnas:
        op.drop_column("proyecciones", "firma")
