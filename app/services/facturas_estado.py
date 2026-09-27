"""
Vencimiento automático de facturas.

Una factura PENDIENTE cuya fecha de vencimiento ya pasó se considera VENCIDA.
Ese cambio lo hace el servidor, cada vez que alguna parte del sistema va a leer
facturas (el listado, la auditoría, el resumen, las recomendaciones y el PDF).

Antes lo hacía la pantalla de Facturas al abrirse: si nadie la abría, la base
seguía diciendo "pendiente" y el resumen o el PDF contaban como pendiente una
factura que en realidad ya estaba vencida.
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.factura import Factura, EstadoFactura


ZONA_AR = ZoneInfo("America/Argentina/Buenos_Aires")


def hoy_ar() -> date:
    """Fecha de hoy en Argentina (el servidor corre en UTC)."""
    return datetime.now(ZONA_AR).date()


def inicio_de_hoy() -> datetime:
    """Hoy a las 00:00 UTC, que es como se guardan las fechas de vencimiento.

    Una factura vence recién cuando su fecha de vencimiento "fue superada"
    (HU-06 y HU-08): la que vence hoy sigue pendiente todo el día. Comparar
    contra la hora actual en UTC la daba por vencida el mismo día y, desde las
    21 h de Argentina, también a las que vencen al día siguiente.
    """
    hoy = hoy_ar()
    return datetime(hoy.year, hoy.month, hoy.day, tzinfo=timezone.utc)


def ya_vencio(fecha_vencimiento: datetime) -> bool:
    """True si la fecha de vencimiento es anterior a hoy."""
    if fecha_vencimiento.tzinfo is None:
        fecha_vencimiento = fecha_vencimiento.replace(tzinfo=timezone.utc)
    return fecha_vencimiento < inicio_de_hoy()


def marcar_vencidas(db: Session, usuario_id: int) -> int:
    """Pasa a VENCIDA las pendientes del usuario con el vencimiento pasado.

    Devuelve cuántas cambió. Solo toca PENDIENTE → VENCIDA, que es una
    transición válida de la máquina de estados (ver routers/facturas.py).
    """
    cambiadas = (
        db.query(Factura)
        .filter(
            Factura.usuario_id == usuario_id,
            Factura.estado == EstadoFactura.PENDIENTE,
            Factura.fecha_vencimiento < inicio_de_hoy(),
        )
        .update({Factura.estado: EstadoFactura.VENCIDA}, synchronize_session="fetch")
    )
    if cambiadas:
        db.commit()
    return cambiadas
