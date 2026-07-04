"""
Router de Alertas de Auditoría — control y monitoreo de inconsistencias.

Expone bajo /alertas la ejecución de la auditoría (que recorre los datos del
usuario en busca de anomalías) y la consulta/gestión de las alertas generadas.
La lógica de detección vive en el servicio de auditoría; este router orquesta.

Endpoints:
  POST  /alertas/ejecutar-auditoria → corre la auditoría y genera alertas.
  GET   /alertas/                   → lista las alertas (con filtros).
  PATCH /alertas/{id}               → marca una alerta como resuelta o la reabre.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
from app.schemas.alerta import AlertaResponse, AlertaResolverUpdate
from app.dependencies import get_current_user
from app.models.gasto import Gasto
from app.services.auditoria import ejecutar_auditoria, detectar_gastos_duplicados


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


@router.delete("/resueltas", status_code=status.HTTP_200_OK)
def limpiar_alertas_resueltas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Borra del historial todas las alertas ya resueltas del usuario.
    Nota: si el problema de fondo sigue existiendo, la próxima auditoría lo
    volverá a detectar (al borrar la huella, deja de estar 'silenciado')."""
    n = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == current_user.id,
        AlertaAuditoria.resuelta == True,
    ).delete()
    db.commit()
    return {"eliminadas": n}


@router.delete("/{alerta_id}/gasto-duplicado", response_model=AlertaResponse)
def eliminar_gasto_duplicado(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Resuelve de raíz una alerta de gasto duplicado: elimina el gasto repetido
    (el más reciente del par) y marca la alerta como resuelta. Al desaparecer la
    condición, la auditoría tampoco la vuelve a detectar."""
    alerta = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.id == alerta_id,
        AlertaAuditoria.usuario_id == current_user.id,
    ).first()

    if not alerta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerta no encontrada")

    if alerta.tipo != TipoAlerta.GASTO_DUPLICADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta acción solo aplica a alertas de gasto duplicado",
        )

    # Localizamos el gasto repetido a eliminar. Las alertas nuevas guardan la
    # referencia directa (gasto_id_duplicado, migración 0006), lo que evita
    # borrar el par equivocado cuando dos pares comparten el mismo monto.
    objetivo = None      # el gasto repetido a eliminar (el más reciente del par)
    if alerta.gasto_id_duplicado is not None:
        objetivo = db.query(Gasto).filter(
            Gasto.id == alerta.gasto_id_duplicado,
            Gasto.usuario_id == current_user.id,
        ).first()

    if objetivo is None:
        # Compatibilidad: alertas previas a la migración (sin referencia) o
        # cuyo gasto referenciado ya fue borrado a mano → match por monto.
        pares = detectar_gastos_duplicados(db, current_user.id)
        for gasto_a, gasto_b in pares:
            if alerta.monto_involucrado is not None and float(gasto_a.monto) == float(alerta.monto_involucrado):
                objetivo = gasto_b
                break

    if objetivo is not None:
        db.delete(objetivo)
        db.flush()
        # Recalculamos los pares y desmarcamos todos los gastos del usuario
        # que ya no integren ninguno (no solo el sobreviviente de este par).
        ids_dup = {g.id for par in detectar_gastos_duplicados(db, current_user.id) for g in par}
        marcados = db.query(Gasto).filter(
            Gasto.usuario_id == current_user.id,
            Gasto.es_duplicado == True,
        ).all()
        for g in marcados:
            if g.id not in ids_dup:
                g.es_duplicado = False

    alerta.resuelta = True
    db.commit()
    db.refresh(alerta)
    return alerta
