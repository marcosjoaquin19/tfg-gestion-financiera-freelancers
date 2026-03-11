from fastapi import APIRouter, Depends, HTTPException, status, Query
# Query → para parámetros opcionales de query string, ej: ?categoria=Desarrollo&limite=20

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.schemas.ingreso import IngresoCreate, IngresoResponse
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/ingresos",
    tags=["Ingresos"],
)


# -------------------------------------------------------------------
# POST /ingresos
# Registra un nuevo ingreso para el usuario autenticado
# -------------------------------------------------------------------
@router.post(
    "/",
    response_model=IngresoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_ingreso(
    datos: IngresoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    # get_current_user valida el JWT y devuelve el usuario autenticado
    # si el token es inválido, FastAPI rechaza el request antes de llegar acá
):
    nuevo_ingreso = Ingreso(
        usuario_id=current_user.id,
        # el ingreso siempre pertenece al usuario del token, nunca al del body
        # esto evita que un usuario pueda crear ingresos a nombre de otro
        descripcion=datos.descripcion,
        monto=datos.monto,
        categoria=datos.categoria,
        fecha=datos.fecha,
    )

    db.add(nuevo_ingreso)
    db.commit()
    db.refresh(nuevo_ingreso)
    return nuevo_ingreso


# -------------------------------------------------------------------
# GET /ingresos
# Lista los ingresos del usuario autenticado con filtros opcionales
# -------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[IngresoResponse],
    # devuelve una lista de ingresos
)
def listar_ingresos(
    categoria: str | None = Query(default=None),
    # ?categoria=Desarrollo → filtra por categoría, opcional
    limite: int = Query(default=50, ge=1, le=200),
    # ?limite=20 → cuántos resultados devolver, entre 1 y 200
    offset: int = Query(default=0, ge=0),
    # ?offset=50 → desde qué posición empezar (para paginación)
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(Ingreso).filter(Ingreso.usuario_id == current_user.id)
    # filtramos siempre por usuario → cada uno solo ve sus propios ingresos

    if categoria:
        query = query.filter(Ingreso.categoria == categoria)
        # si mandaron ?categoria=X, agregamos ese filtro adicional

    ingresos = query.order_by(Ingreso.fecha.desc()).offset(offset).limit(limite).all()
    # order_by fecha descendente → los más recientes primero

    return ingresos


# -------------------------------------------------------------------
# GET /ingresos/{ingreso_id}
# Devuelve un ingreso específico por su ID
# -------------------------------------------------------------------
@router.get(
    "/{ingreso_id}",
    response_model=IngresoResponse,
)
def obtener_ingreso(
    ingreso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ingreso = db.query(Ingreso).filter(
        Ingreso.id == ingreso_id,
        Ingreso.usuario_id == current_user.id,
        # verificamos que el ingreso pertenezca al usuario autenticado
        # sin esto, cualquier usuario podría ver ingresos de otros con solo adivinar el ID
    ).first()

    if not ingreso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingreso no encontrado",
        )

    return ingreso


# -------------------------------------------------------------------
# PUT /ingresos/{ingreso_id}
# Actualiza un ingreso existente
# -------------------------------------------------------------------
@router.put(
    "/{ingreso_id}",
    response_model=IngresoResponse,
)
def actualizar_ingreso(
    ingreso_id: int,
    datos: IngresoCreate,
    # reutilizamos IngresoCreate → mismos campos y validaciones
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ingreso = db.query(Ingreso).filter(
        Ingreso.id == ingreso_id,
        Ingreso.usuario_id == current_user.id,
    ).first()

    if not ingreso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingreso no encontrado",
        )

    ingreso.descripcion = datos.descripcion
    ingreso.monto = datos.monto
    ingreso.categoria = datos.categoria
    ingreso.fecha = datos.fecha

    db.commit()
    db.refresh(ingreso)
    return ingreso


# -------------------------------------------------------------------
# DELETE /ingresos/{ingreso_id}
# Elimina un ingreso del usuario autenticado
# -------------------------------------------------------------------
@router.delete(
    "/{ingreso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    # 204 No Content → operación exitosa pero no hay nada que devolver
)
def eliminar_ingreso(
    ingreso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ingreso = db.query(Ingreso).filter(
        Ingreso.id == ingreso_id,
        Ingreso.usuario_id == current_user.id,
    ).first()

    if not ingreso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingreso no encontrado",
        )

    db.delete(ingreso)
    db.commit()
