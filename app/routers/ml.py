from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.usuario import Usuario
from app.services import ml_service

router = APIRouter(prefix="/ml", tags=["ML"])

CATEGORIAS_VALIDAS = ml_service.CATEGORIAS_VALIDAS


class CorregirRequest(BaseModel):
    descripcion: str
    categoria_correcta: str


@router.get("/estado")
def estado_modelo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return ml_service.obtener_estado_modelo(db, current_user.id)


@router.post("/reentrenar")
def reentrenar(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    resultado = ml_service.reentrenar_modelo_usuario(db, current_user.id)
    return resultado


@router.post("/corregir")
def corregir(
    datos: CorregirRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if datos.categoria_correcta not in CATEGORIAS_VALIDAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Categoría inválida. Opciones: {', '.join(CATEGORIAS_VALIDAS)}",
        )

    ml_service.registrar_ejemplo(datos.descripcion, datos.categoria_correcta, db, current_user.id)
    resultado = ml_service.reentrenar_modelo_usuario(db, current_user.id)
    estado = ml_service.obtener_estado_modelo(db, current_user.id)

    return {
        "mensaje": "Modelo actualizado con tu corrección",
        "nuevo_estado": estado,
        **resultado,
    }
