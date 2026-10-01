"""
Router de Proyecciones — predicción de ingresos futuros.

Expone los endpoints bajo /proyecciones. La lógica de predicción (modelo
Prophet) vive en prophet_service; este router solo recibe los pedidos del
frontend, valida el usuario autenticado y devuelve/consulta las proyecciones.

Endpoints:
  POST /proyecciones/generar  → calcula y guarda N períodos de proyección.
  GET  /proyecciones/         → lista las proyecciones vigentes del usuario.
  GET  /proyecciones/historico → serie mensual con la que se entrena el modelo.
  GET  /proyecciones/{id}     → devuelve una proyección puntual.
"""

from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.proyeccion import Proyeccion
from app.schemas.proyeccion import ProyeccionResponse, ProyeccionGenerarRequest, HistoricoResponse
from app.dependencies import get_current_user
from app.models.ingreso import Ingreso
from app.services.prophet_service import (
    asegurar_proyecciones_vigentes,
    generar_proyecciones as _generar_proyecciones,
    inicio_mes_en_curso,
    serie_mensual,
)


router = APIRouter(prefix="/proyecciones", tags=["Proyecciones"])


# POST /proyecciones/generar
# Genera las proyecciones de ingresos para los próximos `periodos` y las guarda.
@router.post("/generar", response_model=list[ProyeccionResponse], status_code=status.HTTP_201_CREATED)
def generar(
    datos: ProyeccionGenerarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return _generar_proyecciones(db, current_user.id, datos.periodos)


# GET /proyecciones/
# Lista las proyecciones del usuario, ordenadas por fecha. Si tiene ingresos,
# antes se asegura de que estén calculadas y al día (como el semáforo): con el
# demo recién sembrado, el Dashboard pedía la lista antes de que nadie la
# calculara y mostraba "Proyección próx. mes: $ 0".
@router.get("/", response_model=list[ProyeccionResponse])
def listar_proyecciones(
    limite: int = Query(default=30, ge=1, le=365),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if db.query(Ingreso.id).filter(Ingreso.usuario_id == current_user.id).first():
        asegurar_proyecciones_vigentes(db, current_user.id)

    proyecciones = db.query(Proyeccion).filter(
        Proyeccion.usuario_id == current_user.id
    ).order_by(Proyeccion.fecha_proyeccion.asc()).offset(offset).limit(limite).all()

    return proyecciones


# GET /proyecciones/historico
# La serie mensual que ve el modelo, para que el gráfico muestre exactamente
# eso (antes el frontend sumaba los últimos 200 ingresos por su cuenta).
# Va antes de /{proyeccion_id} para que "historico" no se lea como un id.
@router.get("/historico", response_model=HistoricoResponse)
def historico(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ingresos = db.query(Ingreso).filter(Ingreso.usuario_id == current_user.id).all()
    serie, total_en_curso, _ = serie_mensual(ingresos)
    return {
        # en UTC explícito, como el resto de las fechas que devuelve la API
        "meses": [{"mes": mes.replace(tzinfo=timezone.utc), "total": total} for mes, total in serie],
        "mes_en_curso": inicio_mes_en_curso().replace(tzinfo=timezone.utc),
        "total_mes_en_curso": total_en_curso,
    }


# GET /proyecciones/{id}
# Devuelve una proyección puntual; 404 si no existe o no es del usuario.
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
