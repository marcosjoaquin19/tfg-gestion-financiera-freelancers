from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.usuario import Usuario
from app.models.gasto import Gasto
from app.schemas.gasto import GastoCreate, GastoResponse
from app.dependencies import get_current_user
from app.services.ia_service import clasificar_gasto


router = APIRouter(prefix="/gastos", tags=["Gastos"])


class ClasificarRequest(BaseModel):
    descripcion: str


class ClasificarResponse(BaseModel):
    categoria_sugerida: str
    fuente: str | None = None
    confianza: float | None = None


@router.post("/clasificar", response_model=ClasificarResponse)
def clasificar(
    datos: ClasificarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    resultado = clasificar_gasto(datos.descripcion, db, current_user.id)
    return ClasificarResponse(
        categoria_sugerida=resultado["categoria_sugerida"],
        fuente=resultado.get("fuente"),
        confianza=resultado.get("confianza"),
    )


@router.post("/", response_model=GastoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto(
    datos: GastoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    nuevo_gasto = Gasto(
        usuario_id=current_user.id,
        descripcion=datos.descripcion,
        monto=datos.monto,
        categoria=datos.categoria,
        fecha=datos.fecha,
        # es_duplicado arranca en False, el módulo de auditoría lo puede marcar después
    )
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)
    return nuevo_gasto


@router.get("/", response_model=list[GastoResponse])
def listar_gastos(
    categoria: str | None = Query(default=None),
    solo_duplicados: bool = Query(default=False),
    # ?solo_duplicados=true → filtra solo los gastos marcados como duplicados por auditoría
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(Gasto).filter(Gasto.usuario_id == current_user.id)

    if categoria:
        query = query.filter(Gasto.categoria == categoria)

    if solo_duplicados:
        query = query.filter(Gasto.es_duplicado == True)

    return query.order_by(Gasto.fecha.desc()).offset(offset).limit(limite).all()


@router.get("/{gasto_id}", response_model=GastoResponse)
def obtener_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    gasto = db.query(Gasto).filter(
        Gasto.id == gasto_id,
        Gasto.usuario_id == current_user.id,
    ).first()

    if not gasto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado")

    return gasto


@router.put("/{gasto_id}", response_model=GastoResponse)
def actualizar_gasto(
    gasto_id: int,
    datos: GastoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    gasto = db.query(Gasto).filter(
        Gasto.id == gasto_id,
        Gasto.usuario_id == current_user.id,
    ).first()

    if not gasto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado")

    gasto.descripcion = datos.descripcion
    gasto.monto = datos.monto
    gasto.categoria = datos.categoria
    gasto.fecha = datos.fecha

    db.commit()
    db.refresh(gasto)
    return gasto


@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_gasto(
    gasto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    gasto = db.query(Gasto).filter(
        Gasto.id == gasto_id,
        Gasto.usuario_id == current_user.id,
    ).first()

    if not gasto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado")

    db.delete(gasto)
    db.commit()
