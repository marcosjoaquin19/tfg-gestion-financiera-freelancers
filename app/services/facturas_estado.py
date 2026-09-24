"""
Vencimiento automático de facturas.

Una factura PENDIENTE cuya fecha de vencimiento ya pasó se considera VENCIDA.
Ese cambio lo hace el servidor, cada vez que alguna parte del sistema va a leer
facturas (el listado, la auditoría, el resumen, las recomendaciones y el PDF).

Antes lo hacía la pantalla de Facturas al abrirse: si nadie la abría, la base
seguía diciendo "pendiente" y el resumen o el PDF contaban como pendiente una
factura que en realidad ya estaba vencida.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.factura import Factura, EstadoFactura


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
            Factura.fecha_vencimiento < datetime.now(timezone.utc),
        )
        .update({Factura.estado: EstadoFactura.VENCIDA}, synchronize_session="fetch")
    )
    if cambiadas:
        db.commit()
    return cambiadas
