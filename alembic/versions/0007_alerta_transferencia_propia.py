"""alerta de transferencia entre cuentas propias

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-04

Un freelancer argentino opera con varias cuentas (banco tradicional, Mercado
Pago, billeteras). Al importar los extractos de cada una, una transferencia
entre cuentas propias aparece como débito en un archivo y como crédito en el
otro: el sistema la registraba como gasto + ingreso, y ese "ingreso" inflaba
la facturación móvil de 12 meses que evalúa la categoría de Monotributo.

Esta migración habilita el detector de auditoría TRANSFERENCIA_PROPIA:

1. Agrega el valor `TRANSFERENCIA_PROPIA` al enum `tipoalerta`. Igual que en
   la migración 0004, el label va en MAYÚSCULAS porque SQLAlchemy persiste el
   `.name` del miembro Python, y `ALTER TYPE ... ADD VALUE` se ejecuta en un
   bloque autocommit (no soporta transacción en PG viejos), verificando antes
   que no exista para ser idempotente.

2. Agrega `ingreso_id_relacionado` a `alertas_auditoria` (FK a ingresos con
   SET NULL): junto con `gasto_id_duplicado` (que para este tipo de alerta
   referencia la pata de salida), permite descartar la transferencia completa
   —ambas patas— con una sola acción desde la alerta.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NOMBRE = "fk_alertas_auditoria_ingreso_relacionado"


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # ── Enum tipoalerta: agregar TRANSFERENCIA_PROPIA ─────────────────────
    if conn.dialect.name == "postgresql":
        existe = conn.execute(
            sa.text(
                "SELECT 1 FROM pg_enum e "
                "JOIN pg_type t ON t.oid = e.enumtypid "
                "WHERE t.typname = 'tipoalerta' AND e.enumlabel = 'TRANSFERENCIA_PROPIA'"
            )
        ).scalar()
        if not existe:
            with op.get_context().autocommit_block():
                op.execute("ALTER TYPE tipoalerta ADD VALUE 'TRANSFERENCIA_PROPIA'")

    # ── alertas_auditoria: columna ingreso_id_relacionado ─────────────────
    if not inspector.has_table("alertas_auditoria"):
        return

    columnas = {c["name"] for c in inspector.get_columns("alertas_auditoria")}
    if "ingreso_id_relacionado" not in columnas:
        op.add_column(
            "alertas_auditoria",
            sa.Column("ingreso_id_relacionado", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            FK_NOMBRE,
            "alertas_auditoria",
            "ingresos",
            ["ingreso_id_relacionado"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    # El valor del enum no se elimina (PostgreSQL no soporta DROP VALUE);
    # solo se revierte la columna.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("alertas_auditoria"):
        return

    columnas = {c["name"] for c in inspector.get_columns("alertas_auditoria")}
    if "ingreso_id_relacionado" in columnas:
        op.drop_constraint(FK_NOMBRE, "alertas_auditoria", type_="foreignkey")
        op.drop_column("alertas_auditoria", "ingreso_id_relacionado")
