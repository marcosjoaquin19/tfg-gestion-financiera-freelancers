"""indices temporales para consultas rolling 12 meses (AFIP)

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-22

Sugerencia del docente sobre la segunda entrega:

> "Dado que la AFIP evalúa los límites de categoría basándose en la
> facturación móvil de los últimos 12 meses, tu backend en FastAPI deberá
> realizar consultas agregadas de series temporales de manera constante.
> Un buen diseño en este punto evitará cuellos de botella en el rendimiento
> cuando la plataforma escale a múltiples usuarios."

Agregamos índices compuestos `(usuario_id, fecha)` en las tres tablas
transaccionales para soportar el patrón típico:

    WHERE usuario_id = ? AND fecha >= ?

que es el corazón de las consultas rolling 12 meses (Monotributo),
reportes mensuales y auditorías por ventana temporal.

El orden de las columnas en el índice no es arbitrario: `usuario_id` va
primero porque es el predicado de igualdad y la cardinalidad real es alta
(muchos usuarios distintos); `fecha` va segundo para acelerar el filtro de
rango sobre las filas ya restringidas al usuario.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDICES = [
    ("ix_ingresos_usuario_fecha", "ingresos", ["usuario_id", "fecha"]),
    ("ix_gastos_usuario_fecha", "gastos", ["usuario_id", "fecha"]),
    ("ix_facturas_usuario_emision", "facturas", ["usuario_id", "fecha_emision"]),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    for nombre, tabla, columnas in INDICES:
        if not inspector.has_table(tabla):
            continue
        existentes = {idx["name"] for idx in inspector.get_indexes(tabla)}
        if nombre not in existentes:
            op.create_index(nombre, tabla, columnas)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    for nombre, tabla, _ in INDICES:
        if not inspector.has_table(tabla):
            continue
        existentes = {idx["name"] for idx in inspector.get_indexes(tabla)}
        if nombre in existentes:
            op.drop_index(nombre, table_name=tabla)
