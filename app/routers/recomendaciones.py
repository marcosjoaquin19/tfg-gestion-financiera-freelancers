"""
Router de Recomendaciones — consejos financieros para el freelancer.

Expone GET /recomendaciones. Las recomendaciones son determinísticas: se
calculan a partir de los datos reales del usuario (ingresos, gastos, facturas,
monotributo) con reglas definidas en ia_service, sin texto generado por IA.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.dependencies import get_current_user
from app.services.ia_service import generar_recomendaciones

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])


# GET /recomendaciones/
# Devuelve la lista de recomendaciones calculadas para el usuario autenticado.
@router.get("/")
def recomendaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return generar_recomendaciones(usuario_id=current_user.id, db=db)
