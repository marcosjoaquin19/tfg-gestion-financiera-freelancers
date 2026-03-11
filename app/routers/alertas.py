from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
from app.schemas.alerta import AlertaResponse, AlertaResolverUpdate
from app.dependencies import get_current_user
from app.services.auditoria import ejecutar_auditoria


router = APIRouter(prefix="/alertas", tags=["Alertas de Auditoría"])


@router.post("/ejecutar-auditoria", status_code=status.HTTP_200_OK)
def ejecutar_auditoria_endpoint(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # analiza los gastos y facturas del usuario y genera alertas nuevas
    conteo = ejecutar_auditoria(db, usuario_id=current_user.id)
    total = sum(conteo.values())
    return {
        "mensaje": f"Auditoría completada. {total} alertas generadas.",
        "detalle": conteo,
    }


@router.get("/", response_model=list[AlertaResponse])
def listar_alertas(
    tipo: TipoAlerta | None = Query(default=None),
    # ?tipo=gasto_duplicado / ?tipo=anomalia_estadistica / ?tipo=discrepancia_facturacion
    solo_pendientes: bool = Query(default=True),
    # por defecto solo muestra las alertas no resueltas
    # ?solo_pendientes=false → muestra todas incluyendo las ya revisadas
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(AlertaAuditoria).filter(AlertaAuditoria.usuario_id == current_user.id)

    if tipo:
        query = query.filter(AlertaAuditoria.tipo == tipo)

    if solo_pendientes:
        query = query.filter(AlertaAuditoria.resuelta == False)

    return query.order_by(AlertaAuditoria.fecha_deteccion.desc()).offset(offset).limit(limite).all()


@router.get("/{alerta_id}", response_model=AlertaResponse)
def obtener_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    alerta = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.id == alerta_id,
        AlertaAuditoria.usuario_id == current_user.id,
    ).first()

    if not alerta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")

    return alerta


@router.patch("/{alerta_id}/resolver", response_model=AlertaResponse)
def resolver_alerta(
    alerta_id: int,
    datos: AlertaResolverUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # PATCH → solo actualizamos el campo resuelta
    # el usuario no puede crear ni editar alertas, solo marcarlas como revisadas
    alerta = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.id == alerta_id,
        AlertaAuditoria.usuario_id == current_user.id,
    ).first()

    if not alerta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")

    alerta.resuelta = datos.resuelta
    db.commit()
    db.refresh(alerta)
    return alerta
