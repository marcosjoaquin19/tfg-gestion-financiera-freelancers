"""referencia directa al gasto duplicado en alertas de auditoría

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-04

Las alertas de tipo GASTO_DUPLICADO localizaban el gasto repetido comparando
el monto de la alerta contra los pares detectados. Si dos pares distintos
compartían el mismo importe, la acción "eliminar gasto duplicado" podía borrar
el gasto del par equivocado.

Esta migración agrega `gasto_id_duplicado`: la auditoría guarda la referencia
directa al gasto repetido (el más reciente del par) al momento de crear la
alerta, y el endpoint de eliminación la usa sin ambigüedad. La columna es
nullable y con ON DELETE SET NULL: si el usuario borra ese gasto por su
cuenta, la alerta queda sin referencia y el endpoint cae al match por monto
(compatibilidad con alertas generadas antes de esta migración).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NOMBRE = "fk_alertas_auditoria_gasto_duplicado"


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("alertas_auditoria"):
        return

    columnas = {c["name"] for c in inspector.get_columns("alertas_auditoria")}
    if "gasto_id_duplicado" not in columnas:
        op.add_column(
            "alertas_auditoria",
            sa.Column("gasto_id_duplicado", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            FK_NOMBRE,
            "alertas_auditoria",
            "gastos",
            ["gasto_id_duplicado"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("alertas_auditoria"):
        return

    columnas = {c["name"] for c in inspector.get_columns("alertas_auditoria")}
    if "gasto_id_duplicado" in columnas:
        op.drop_constraint(FK_NOMBRE, "alertas_auditoria", type_="foreignkey")
        op.drop_column("alertas_auditoria", "gasto_id_duplicado")
