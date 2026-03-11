from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.proyeccion import Proyeccion
from app.schemas.proyeccion import ProyeccionResponse, ProyeccionGenerarRequest
from app.dependencies import get_current_user
from app.services.prophet_service import generar_proyecciones as _generar_proyecciones


router = APIRouter(prefix="/proyecciones", tags=["Proyecciones"])


@router.post("/generar", response_model=list[ProyeccionResponse], status_code=status.HTTP_201_CREATED)
def generar(
    datos: ProyeccionGenerarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return _generar_proyecciones(db, current_user.id, datos.periodos)


@router.get("/", response_model=list[ProyeccionResponse])
def listar_proyecciones(
    limite: int = Query(default=30, ge=1, le=365),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    proyecciones = db.query(Proyeccion).filter(
        Proyeccion.usuario_id == current_user.id
    ).order_by(Proyeccion.fecha_proyeccion.asc()).offset(offset).limit(limite).all()

    return proyecciones


@router.get("/{proyeccion_id}", response_model=ProyeccionResponse)
def obtener_proyeccion(
    proyeccion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    proyeccion = db.query(Proyeccion).filter(
        Proyeccion.id == proyeccion_id,
        Proyeccion.usuario_id == current_user.id,
    ).first()

    if not proyeccion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyección no encontrada")

    return proyeccion
