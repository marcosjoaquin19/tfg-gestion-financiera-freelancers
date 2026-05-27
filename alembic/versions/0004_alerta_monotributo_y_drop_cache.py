"""alerta MONOTRIBUTO_IMPAGO + cache_clasificacion por usuario

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-22

Cambios:
- Agrega el valor `monotributo_impago` al enum tipoalerta. Antes la alerta
  de pago de Monotributo faltante se persistía con `factura_impaga`,
  reusando el tipo de "factura sin cobrar". Ahora tiene tipo propio.
- Recrea `cache_clasificacion` con columna `usuario_id` y UNIQUE compuesto
  por (usuario_id, descripcion_normalizada). La tabla pasa de ser caché
  global de respuestas de Groq (rol anterior, en desuso desde la migración
  al clasificador local) a almacén de correcciones explícitas por usuario
  que alimentan el reentrenamiento del clasificador NLP local.

  La tabla original estaba vacía en uso real (era write-only), por eso es
  seguro recrearla en lugar de hacer ALTER + DROP CONSTRAINT incremental.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ── Enum tipoalerta: agregar MONOTRIBUTO_IMPAGO ───────────────────────
    # `ALTER TYPE ... ADD VALUE` no soporta ejecutarse dentro de una
    # transacción en versiones antiguas de PostgreSQL. Usamos autocommit
    # aislado y verificamos antes que el valor no exista para ser idempotentes.
    if conn.dialect.name == "postgresql":
        existe = conn.execute(
            sa.text(
                "SELECT 1 FROM pg_enum e "
                "JOIN pg_type t ON t.oid = e.enumtypid "
                "WHERE t.typname = 'tipoalerta' AND e.enumlabel = 'monotributo_impago'"
            )
        ).scalar()
        if not existe:
            with op.get_context().autocommit_block():
                op.execute("ALTER TYPE tipoalerta ADD VALUE 'monotributo_impago'")

    # ── cache_clasificacion: recrear con usuario_id ───────────────────────
    if inspector.has_table("cache_clasificacion"):
        op.drop_table("cache_clasificacion")

    op.create_table(
        "cache_clasificacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=True,
        ),
        sa.Column("descripcion_normalizada", sa.String(), nullable=False),
        sa.Column("categoria", sa.String(), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "usuario_id", "descripcion_normalizada",
            name="uq_cache_usuario_desc",
        ),
    )
    op.create_index(
        "ix_cache_clasificacion_id", "cache_clasificacion", ["id"],
    )
    op.create_index(
        "ix_cache_clasificacion_usuario_id",
        "cache_clasificacion", ["usuario_id"],
    )
    op.create_index(
        "ix_cache_clasificacion_descripcion_normalizada",
        "cache_clasificacion", ["descripcion_normalizada"],
    )


def downgrade() -> None:
    # Volvemos a la forma anterior (sin usuario_id, UNIQUE solo en
    # descripcion_normalizada). El valor de enum monotributo_impago no se
    # puede remover en PostgreSQL sin recrear el tipo entero, así que el
    # downgrade lo deja en su lugar — es inerte si el código ya no lo usa.
    op.drop_table("cache_clasificacion")
    op.create_table(
        "cache_clasificacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("descripcion_normalizada", sa.String(), unique=True, nullable=False),
        sa.Column("categoria", sa.String(), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_cache_clasificacion_descripcion_normalizada",
        "cache_clasificacion",
        ["descripcion_normalizada"],
        unique=True,
    )
