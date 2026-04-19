"""tabla_modelo_clasificador

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table("modelos_clasificador"):
        return

    op.create_table(
        "modelos_clasificador",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("modelo_serializado", sa.Text(), nullable=False),
        sa.Column("algoritmo", sa.String(20), nullable=False),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("n_ejemplos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "fecha_entrenamiento",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_modelos_clasificador_id", "modelos_clasificador", ["id"])
    op.create_index("ix_modelos_clasificador_usuario_id", "modelos_clasificador", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_modelos_clasificador_usuario_id", table_name="modelos_clasificador")
    op.drop_index("ix_modelos_clasificador_id", table_name="modelos_clasificador")
    op.drop_table("modelos_clasificador")
