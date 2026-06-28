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

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.factura import Factura, EstadoFactura
from app.schemas.factura import FacturaCreate, FacturaUpdate, FacturaEstadoUpdate, FacturaResponse
from app.dependencies import get_current_user


router = APIRouter(prefix="/facturas", tags=["Facturas"])


# Helper interno: busca una factura del usuario o corta con un error 404.
# Evita repetir esta misma validación en cada endpoint.
def _get_factura_or_404(factura_id: int, db: Session, usuario_id: int) -> Factura:
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

    if datos.estado == EstadoFactura.PAGADA and datos.fecha_pago is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe indicar la fecha de pago al marcar una factura como pagada",
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
