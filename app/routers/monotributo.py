from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioResponse, UsuarioUpdateMonotributo
from app.dependencies import get_current_user
from app.services.monotributo_service import (
    calcular_estado_monotributo,
    verificar_pago_monotributo,
    CATEGORIAS_SERVICIOS,
)

router = APIRouter(prefix="/monotributo", tags=["Monotributo"])


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
    if cat not in CATEGORIAS_SERVICIOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría inválida. Opciones válidas: {', '.join(CATEGORIAS_SERVICIOS.keys())}",
        )
    current_user.categoria_monotributo = cat
    db.commit()
    db.refresh(current_user)
    return current_user
