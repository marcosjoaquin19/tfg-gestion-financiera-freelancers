"""tabla_categoria_monotributo

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table("categorias_monotributo"):
        return

    op.create_table(
        "categorias_monotributo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("letra", sa.String(2), nullable=False),
        sa.Column("limite_anual", sa.Numeric(15, 2), nullable=False),
        sa.Column("cuota_mensual", sa.Numeric(12, 2), nullable=False),
        sa.Column("actividad", sa.String(20), nullable=False, server_default="servicios"),
        sa.Column("fecha_vigencia", sa.Date(), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_categorias_monotributo_letra", "categorias_monotributo", ["letra"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_categorias_monotributo_letra", table_name="categorias_monotributo")
    op.drop_table("categorias_monotributo")
