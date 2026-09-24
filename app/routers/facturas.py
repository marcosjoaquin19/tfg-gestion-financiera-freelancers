"""
Router de Facturas — emisión y seguimiento de facturas.

Expone el CRUD de facturas bajo /facturas. Cada factura tiene un estado
(pendiente / pagada / vencida) y reglas de negocio: una factura ya pagada no
se puede editar ni eliminar, y al marcarla como pagada hay que indicar la fecha
de cobro. Todas las operaciones quedan acotadas al usuario autenticado.

Endpoints:
  POST   /facturas/                 → crea una factura (arranca PENDIENTE).
  GET    /facturas/                 → lista con filtros por estado y cliente.
  GET    /facturas/{id}             → devuelve una factura.
  PUT    /facturas/{id}             → edita una factura no pagada.
  PATCH  /facturas/{id}/estado      → cambia solo el estado (ej: a pagada).
  DELETE /facturas/{id}             → elimina una factura no pagada.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.factura import Factura, EstadoFactura
from app.schemas.factura import FacturaCreate, FacturaUpdate, FacturaEstadoUpdate, FacturaResponse
from app.dependencies import get_current_user
from app.services.facturas_estado import marcar_vencidas


router = APIRouter(prefix="/facturas", tags=["Facturas"])


# PATRÓN: State — transiciones admitidas del ciclo de vida de una factura.
# PAGADA es un estado terminal: sin esto, un PATCH podía revertir una factura
# cobrada a pendiente y borrar de paso su fecha de pago, mientras que PUT y
# DELETE sí la protegían. La puerta tiene que estar cerrada por los tres lados.
# VENCIDA → PENDIENTE no es manual: ocurre sola al editar el vencimiento a
# una fecha futura (ver editar_factura).
TRANSICIONES_VALIDAS = {
    EstadoFactura.PENDIENTE: {EstadoFactura.PAGADA, EstadoFactura.VENCIDA},
    EstadoFactura.VENCIDA:   {EstadoFactura.PAGADA},
    EstadoFactura.PAGADA:    set(),
}


def _en_utc(fecha: datetime) -> datetime:
    """Las fechas guardadas vienen con zona horaria y las que manda la
    pantalla no ("2026-09-01T00:00:00"). Para compararlas se lleva todo a UTC,
    que es como se guardan."""
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def _ya_vencio(factura: Factura) -> bool:
    return _en_utc(factura.fecha_vencimiento) < datetime.now(timezone.utc)


# Helper interno: busca una factura del usuario o corta con un error 404.
# Evita repetir esta misma validación en cada endpoint.
def _get_factura_or_404(factura_id: int, db: Session, usuario_id: int) -> Factura:
    marcar_vencidas(db, usuario_id)
    factura = db.query(Factura).filter(
        Factura.id == factura_id,
        Factura.usuario_id == usuario_id,
    ).first()
    if not factura:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    return factura


@router.post("/", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
def crear_factura(
    datos: FacturaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    nueva_factura = Factura(
        usuario_id=current_user.id,
        cliente_nombre=datos.cliente_nombre,
        descripcion=datos.descripcion,
        monto=datos.monto,
        fecha_emision=datos.fecha_emision,
        fecha_vencimiento=datos.fecha_vencimiento,
        # estado arranca en PENDIENTE por defecto (definido en el modelo)
    )
    db.add(nueva_factura)
    db.commit()
    db.refresh(nueva_factura)
    return nueva_factura


@router.get("/", response_model=list[FacturaResponse])
def listar_facturas(
    estado: EstadoFactura | None = Query(default=None),
    # ?estado=pendiente / ?estado=pagada / ?estado=vencida
    cliente_nombre: str | None = Query(default=None),
    # ?cliente_nombre=Acme → filtra por nombre de cliente
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Antes de filtrar por estado: así ?estado=vencida ya incluye las que
    # vencieron desde la última consulta.
    marcar_vencidas(db, current_user.id)
    query = db.query(Factura).filter(Factura.usuario_id == current_user.id)

    if estado:
        query = query.filter(Factura.estado == estado)

    if cliente_nombre:
        query = query.filter(Factura.cliente_nombre.ilike(f"%{cliente_nombre}%"))
        # ilike → búsqueda case-insensitive, ej: "acme" matchea "Acme Corp"

    return query.order_by(Factura.fecha_emision.desc()).offset(offset).limit(limite).all()


@router.get("/{factura_id}", response_model=FacturaResponse)
def obtener_factura(
    factura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return _get_factura_or_404(factura_id, db, current_user.id)


@router.put("/{factura_id}", response_model=FacturaResponse)
def editar_factura(
    factura_id: int,
    datos: FacturaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    factura = _get_factura_or_404(factura_id, db, current_user.id)

    if factura.estado == EstadoFactura.PAGADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede editar una factura ya pagada",
        )

    factura.cliente_nombre = datos.cliente_nombre
    factura.descripcion = datos.descripcion
    factura.monto = datos.monto
    factura.fecha_emision = datos.fecha_emision
    factura.fecha_vencimiento = datos.fecha_vencimiento

    # El estado acompaña al nuevo vencimiento. Caso típico: el cliente pide
    # más plazo y se corre la fecha; antes la factura quedaba "vencida" para
    # siempre, porque vencida → pendiente no es una transición manual.
    if factura.estado == EstadoFactura.VENCIDA and not _ya_vencio(factura):
        factura.estado = EstadoFactura.PENDIENTE
    elif factura.estado == EstadoFactura.PENDIENTE and _ya_vencio(factura):
        factura.estado = EstadoFactura.VENCIDA

    db.commit()
    db.refresh(factura)
    return factura


@router.patch("/{factura_id}/estado", response_model=FacturaResponse)
def actualizar_estado_factura(
    factura_id: int,
    datos: FacturaEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # PATCH en vez de PUT → solo actualizamos el estado, no toda la factura
    # una factura emitida no debería poder modificar cliente, monto o fechas
    factura = _get_factura_or_404(factura_id, db, current_user.id)

    if factura.estado == EstadoFactura.PAGADA:
        # Estado terminal: ni siquiera "pagada → pagada", que servía para
        # cambiarle la fecha de cobro a una factura que se supone cerrada.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La factura ya está pagada: no se puede modificar su estado ni su fecha de pago",
        )

    destinos_validos = TRANSICIONES_VALIDAS[factura.estado]
    if datos.estado != factura.estado and datos.estado not in destinos_validos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Transición de estado inválida: {factura.estado.value} → {datos.estado.value}. "
                "Para volver a pendiente una factura vencida, editá su fecha de vencimiento."
            ),
        )

    if datos.estado == EstadoFactura.VENCIDA and not _ya_vencio(factura):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La factura todavía no venció: no se puede marcar como vencida",
        )

    if datos.estado == EstadoFactura.PAGADA:
        if datos.fecha_pago is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe indicar la fecha de pago al marcar una factura como pagada",
            )
        # Se compara por día: una factura se puede cobrar el mismo día que se emite.
        if _en_utc(datos.fecha_pago).date() < _en_utc(factura.fecha_emision).date():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La fecha de pago no puede ser anterior a la fecha de emisión",
            )

    factura.estado = datos.estado
    factura.fecha_pago = datos.fecha_pago

    db.commit()
    db.refresh(factura)
    return factura


@router.delete("/{factura_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_factura(
    factura_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    factura = _get_factura_or_404(factura_id, db, current_user.id)

    if factura.estado == EstadoFactura.PAGADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una factura ya pagada",
        )

    db.delete(factura)
    db.commit()
