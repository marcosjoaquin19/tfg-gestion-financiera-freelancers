"""
Router de Machine Learning — clasificador de gastos.

Expone bajo /ml las operaciones del clasificador que asigna una categoría a un
gasto a partir de su descripción. Permite consultar el estado del modelo,
reentrenarlo con los datos del usuario y registrar correcciones manuales (que
mejoran el modelo personalizado). El entrenamiento corre 100% local.

Endpoints:
  GET  /ml/estado     → info del modelo activo (algoritmo, precisión, ejemplos).
  POST /ml/reentrenar → reentrena el modelo con los gastos del usuario.
  POST /ml/corregir   → registra una corrección y reentrena al instante.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.usuario import Usuario
from app.services import ml_service

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


@router.post("/corregir")
def corregir(
    datos: CorregirRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Registra una corrección explícita del usuario sobre una clasificación
    del playground y dispara el reentrenamiento del modelo. La corrección se
    persiste por usuario y entra como ejemplo de entrenamiento en el próximo
    fit, sin necesidad de que el usuario haya creado un gasto real."""
    if datos.categoria_correcta not in CATEGORIAS_VALIDAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Categoría inválida. Opciones: {', '.join(CATEGORIAS_VALIDAS)}",
        )

    ml_service.registrar_ejemplo(datos.descripcion, datos.categoria_correcta, db, current_user.id)
    resultado = ml_service.reentrenar_modelo_usuario(db, current_user.id)
    estado = ml_service.obtener_estado_modelo(db, current_user.id)

    # El detalle del reentrenamiento va bajo su propia clave: si se expandiera
    # con **resultado sobre este diccionario, su "mensaje" pisaría el de
    # confirmación y el usuario leería "pocos ejemplos propios" justo después
    # de que su corrección se guardó correctamente.
    return {
        "mensaje": "Modelo actualizado con tu corrección",
        "nuevo_estado": estado,
        "detalle_entrenamiento": resultado,
    }
