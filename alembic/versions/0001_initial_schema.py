"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-21

Crea todas las tablas del proyecto desde cero.
Si la base de datos ya tiene las tablas (instalación previa sin Alembic),
la migración detecta que existen y no hace nada, evitando errores.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Si la tabla principal ya existe, la BD fue inicializada antes de Alembic.
    # Marcamos la migración como aplicada sin tocar nada.
    if inspector.has_table("usuarios"):
        return

    # ── Enums de PostgreSQL ───────────────────────────────────────────────────
    estadofactura = sa.Enum(
        "pendiente", "pagada", "vencida",
        name="estadofactura",
    )
    tipoalerta = sa.Enum(
        "gasto_duplicado",
        "anomalia_estadistica",
        "discrepancia_facturacion",
        "riesgo_recategorizacion",
        "factura_impaga",
        "comision_excesiva",
        name="tipoalerta",
    )
    estadofactura.create(conn, checkfirst=True)
    tipoalerta.create(conn, checkfirst=True)

    # ── Tabla: usuarios ───────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("email", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("es_activo", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("categoria_monotributo", sa.String(2), nullable=True),
        sa.Column("actividad_monotributo", sa.String(20), server_default="servicios"),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── Tabla: ingresos ───────────────────────────────────────────────────────
    op.create_table(
        "ingresos",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── Tabla: gastos ─────────────────────────────────────────────────────────
    op.create_table(
        "gastos",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("es_duplicado", sa.Boolean(), server_default=sa.text("false")),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── Tabla: facturas ───────────────────────────────────────────────────────
    op.create_table(
        "facturas",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column("cliente_nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.String(500), nullable=False),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "estado",
            sa.Enum(
                "pendiente", "pagada", "vencida",
                name="estadofactura",
                create_type=False,  # ya creado arriba
            ),
            server_default="pendiente",
        ),
        sa.Column("fecha_emision", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_vencimiento", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_pago", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── Tabla: proyecciones ───────────────────────────────────────────────────
    op.create_table(
        "proyecciones",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "fecha_proyeccion",
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        sa.Column("monto_proyectado", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_lower", sa.Numeric(12, 2), nullable=False),
        sa.Column("monto_upper", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "fecha_generacion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── Tabla: alertas_auditoria ──────────────────────────────────────────────
    op.create_table(
        "alertas_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tipo",
            sa.Enum(
                "gasto_duplicado",
                "anomalia_estadistica",
                "discrepancia_facturacion",
                "riesgo_recategorizacion",
                "factura_impaga",
                "comision_excesiva",
                name="tipoalerta",
                create_type=False,  # ya creado arriba
            ),
            nullable=False,
        ),
        sa.Column("descripcion", sa.String(500), nullable=False),
        sa.Column("monto_involucrado", sa.Numeric(12, 2), nullable=True),
        sa.Column("resuelta", sa.Boolean(), server_default=sa.text("false")),
        sa.Column(
            "fecha_deteccion",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── Tabla: cache_clasificacion ────────────────────────────────────────────
    op.create_table(
        "cache_clasificacion",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "descripcion_normalizada",
            sa.String(),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column("categoria", sa.String(), nullable=False),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("cache_clasificacion")
    op.drop_table("alertas_auditoria")
    op.drop_table("proyecciones")
    op.drop_table("facturas")
    op.drop_table("gastos")
    op.drop_table("ingresos")
    op.drop_table("usuarios")
    sa.Enum(name="tipoalerta").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estadofactura").drop(op.get_bind(), checkfirst=True)
