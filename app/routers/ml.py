"""
Router de Machine Learning — clasificador de gastos.

Expone bajo /ml las operaciones del clasificador que asigna una categoría a un
gasto a partir de su descripción. Permite consultar el estado del modelo,
reentrenarlo con los datos del usuario y registrar correcciones manuales (que
mejoran el modelo personalizado). El entrenamiento corre 100% local.

Endpoints:
  GET  /ml/estado     → info del modelo activo (algoritmo, precisión, ejemplos).
  POST /ml/reentrenar → reentrena el modelo con los gastos del usuario.
  POST /ml/corregir   → registra una corrección (se aplica al instante) y
                        reentrena el modelo en segundo plano.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.dependencies import get_current_user
from app.models.usuario import Usuario
from app.services import ml_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ML"])

CATEGORIAS_VALIDAS = ml_service.CATEGORIAS_VALIDAS


# Cuerpo del request para corregir una clasificación desde el playground.
class CorregirRequest(BaseModel):
    descripcion: str = Field(max_length=255)
    # Mismo tope que la descripción de un gasto: una corrección enseña al
    # modelo sobre descripciones de gastos, no tiene sentido que sea más larga.
    categoria_correcta: str

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v):
        # Una corrección en blanco se guardaba como regla "texto vacío →
        # categoría X": desde ahí, cualquier descripción en blanco salía
        # clasificada con 100% de confianza.
        v = v.strip()
        if not v:
            raise ValueError("La descripción no puede estar vacía")
        return v


# GET /ml/estado
# Devuelve los datos del modelo activo del usuario (o del modelo base).
@router.get("/estado")
def estado_modelo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return ml_service.obtener_estado_modelo(db, current_user.id)


# POST /ml/reentrenar
# Reentrena el modelo personal del usuario con sus gastos y correcciones.
@router.post("/reentrenar")
def reentrenar(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return ml_service.reentrenar_modelo_usuario(db, current_user.id)


def _reentrenar_en_segundo_plano(usuario_id: int) -> None:
    """Reentrena el modelo del usuario después de responder.

    HU-05: la respuesta a una corrección se emite de inmediato, sin esperar a
    que el reentrenamiento finalice. La sesión del pedido ya se cerró, así que
    se abre una propia. Si falla, se registra en el log: la corrección ya quedó
    guardada y se aplica igual.
    """
    db = SessionLocal()
    try:
        ml_service.reentrenar_modelo_usuario(db, usuario_id)
    except Exception as e:
        logger.error(f"Falló el reentrenamiento tras una corrección (usuario {usuario_id}): {e}")
    finally:
        db.close()


@router.post("/corregir")
def corregir(
    datos: CorregirRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una corrección explícita del usuario sobre una clasificación
    del playground. La corrección se persiste por usuario y se aplica en la
    próxima clasificación de esa descripción (sin pasar por el modelo); además
    entra como ejemplo de entrenamiento en el reentrenamiento, que corre en
    segundo plano, sin necesidad de que el usuario haya creado un gasto real."""
    if datos.categoria_correcta not in CATEGORIAS_VALIDAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Categoría inválida. Opciones: {', '.join(CATEGORIAS_VALIDAS)}",
        )

    ml_service.registrar_ejemplo(datos.descripcion, datos.categoria_correcta, db, current_user.id)
    background_tasks.add_task(_reentrenar_en_segundo_plano, current_user.id)

    return {
        "mensaje": "Corrección guardada: desde ahora esa descripción se clasifica así. "
                   "El modelo se reentrena en segundo plano.",
        "estado_modelo": ml_service.obtener_estado_modelo(db, current_user.id),
        "reentrenamiento": "en_segundo_plano",
    }
