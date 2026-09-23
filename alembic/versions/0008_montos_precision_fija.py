"""montos con precisión fija (Numeric) en lugar de punto flotante

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-22

Los modelos y la migración inicial declaran los montos como `Numeric(12, 2)`,
es decir, precisión decimal exacta: lo que corresponde a un importe de dinero.
Sin embargo, las bases creadas antes de que existieran las migraciones —entre
ellas la base de demostración— tienen esas columnas como `double precision`,
porque las tablas se habían generado con una versión anterior del modelo y
`create_all` no modifica una tabla que ya existe.

La consecuencia es concreta: en punto flotante, 0,10 + 0,20 da
0,30000000000000004. Sumar centavos deja de ser exacto y los totales pueden
apartarse del valor real por fracciones de centavo que se acumulan.

Esta migración alinea el esquema real con el declarado. Sobre una base creada
desde las migraciones el cambio es un no-op (las columnas ya son `Numeric`);
sobre una base con la deriva, convierte los valores existentes redondeando a
dos decimales, que es la precisión con la que se cargaron.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Columnas de dinero: (tabla, columna, admite nulos)
COLUMNAS_MONETARIAS = [
    ("ingresos", "monto", False),
    ("gastos", "monto", False),
    ("facturas", "monto", False),
    ("proyecciones", "monto_proyectado", False),
    ("proyecciones", "monto_lower", False),
    ("proyecciones", "monto_upper", False),
    ("alertas_auditoria", "monto_involucrado", True),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tablas = set(inspector.get_table_names())

    for tabla, columna, admite_nulos in COLUMNAS_MONETARIAS:
        if tabla not in tablas:
            continue
        op.alter_column(
            tabla,
            columna,
            type_=sa.Numeric(12, 2),
            existing_nullable=admite_nulos,
            # El USING explícito redondea a dos decimales al convertir desde
            # punto flotante; sin él, PostgreSQL rechaza la conversión cuando
            # algún valor tiene más decimales de los que admite la escala.
            postgresql_using=f"ROUND({columna}::numeric, 2)",
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tablas = set(inspector.get_table_names())

    for tabla, columna, admite_nulos in COLUMNAS_MONETARIAS:
        if tabla not in tablas:
            continue
        op.alter_column(
            tabla,
            columna,
            type_=sa.Float(),
            existing_nullable=admite_nulos,
            postgresql_using=f"{columna}::double precision",
        )
