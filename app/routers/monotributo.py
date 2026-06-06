from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.categoria_monotributo import CategoriaMonotributo
from app.schemas.usuario import UsuarioResponse, UsuarioUpdateMonotributo
from app.dependencies import get_current_user
from app.services.monotributo_service import (
    calcular_estado_monotributo,
    verificar_pago_monotributo,
    get_categoria,
)

router = APIRouter(prefix="/monotributo", tags=["Monotributo"])


@router.get("/categorias")
def listar_categorias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Escala vigente de categorías (única fuente de verdad para el frontend).

    Evita duplicar la tabla de montos en el cliente: el front consume esto en
    lugar de tener los valores hardcodeados.
    """
    cats = (
        db.query(CategoriaMonotributo)
        .filter(CategoriaMonotributo.activa == True)
        .order_by(CategoriaMonotributo.limite_anual.asc())
        .all()
    )
    return [
        {
            "letra": c.letra,
            "limite_anual": float(c.limite_anual),
            "cuota_mensual": float(c.cuota_mensual),
            "actividad": c.actividad,
        }
        for c in cats
    ]


@router.get("/estado")
def estado_monotributo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    estado = calcular_estado_monotributo(db, current_user.id)
    if estado is None:
        return {"sin_categoria": True}
    return estado


@router.get("/pago")
def pago_monotributo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return verificar_pago_monotributo(db, current_user.id)


@router.patch("/categoria", response_model=UsuarioResponse)
def actualizar_categoria(
    datos: UsuarioUpdateMonotributo,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    cat = datos.categoria_monotributo.upper()
    if get_categoria(db, cat) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría inválida o no activa: {cat}",
        )
    current_user.categoria_monotributo = cat
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/facturacion-12-meses")
def facturacion_12_meses(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Suma de ingresos del usuario en los últimos 12 meses corridos.

    Es el monto que AFIP usa para evaluar el límite de la categoría de
    Monotributo (facturación móvil de 12 meses). Si el usuario tiene una
    categoría cargada, la respuesta incluye el porcentaje del límite
    anual ya consumido por esa facturación.

    La consulta filtra por `(usuario_id, fecha)` y se apoya en el índice
    compuesto `ix_ingresos_usuario_fecha` agregado en la migración 0005,
    que evita un seq scan sobre toda la tabla `ingresos` y mantiene la
    consulta en O(log n) aunque la plataforma escale a muchos usuarios.
    """
    desde = datetime.now() - timedelta(days=365)
    total = db.query(func.coalesce(func.sum(Ingreso.monto), 0)).filter(
        Ingreso.usuario_id == current_user.id,
        Ingreso.fecha >= desde,
    ).scalar()
    total = float(total or 0)

    info_categoria = None
    if current_user.categoria_monotributo:
        cat = get_categoria(db, current_user.categoria_monotributo)
        if cat is not None:
            limite = float(cat.limite_anual)
            info_categoria = {
                "categoria": cat.letra,
                "limite_anual": limite,
                "porcentaje_usado": round(total / limite * 100, 2) if limite > 0 else 0.0,
            }

    return {
        "facturacion_12_meses": total,
        "desde": desde.date().isoformat(),
        "hasta": datetime.now().date().isoformat(),
        "categoria": info_categoria,
    }
