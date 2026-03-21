from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.dependencies import get_current_user
from app.services.ia_service import generar_recomendaciones

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])


@router.get("/")
def recomendaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return generar_recomendaciones(usuario_id=current_user.id, db=db)
