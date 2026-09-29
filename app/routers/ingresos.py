"""
Router de Ingresos — registro y consulta de ingresos.

Expone el CRUD de ingresos bajo /ingresos. Cada ingreso queda asociado al
usuario autenticado; los ingresos alimentan el cálculo de monotributo, las
proyecciones y el resumen financiero.

Al crear o editar un ingreso se detectan cargas repetidas del mismo cobro
(ver _buscar_ingresos_gemelos). No se bloquea el alta: se marca, porque un
ingreso duplicado infla la facturación de los últimos 12 meses y puede
disparar un cambio de categoría de Monotributo que no corresponde.

Endpoints:
  POST   /ingresos/      → registra un ingreso nuevo.
  GET    /ingresos/      → lista con filtros (categoría, mes y año, paginación).
  GET    /ingresos/meses → meses con ingresos, para el selector de la pantalla.
  GET    /ingresos/{id}  → devuelve un ingreso.
  PUT    /ingresos/{id}  → edita un ingreso.
  DELETE /ingresos/{id}  → elimina un ingreso.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
# Query → para parámetros opcionales de query string, ej: ?categoria=Desarrollo&limite=20

from datetime import datetime, timezone

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.schemas.ingreso import IngresoCreate, IngresoResponse, MesConIngresos
from app.dependencies import get_current_user
from app.services.duplicados_ingreso import (
    _actualizar_marca_duplicado,
    _buscar_ingresos_gemelos,
    _revisar_huerfanos,
)


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

    # Se evalúa después del commit para comparar contra el monto ya guardado:
    # la columna es Numeric(12, 2) y redondea a centavos, así que comparar con
    # el valor que llegó en el pedido podría no coincidir.
    if _actualizar_marca_duplicado(db, nuevo_ingreso):
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
    solo_duplicados: bool = Query(default=False),
    # ?solo_duplicados=true → devuelve únicamente los marcados como repetidos,
    # el mismo filtro que ofrece el listado de gastos
    mes: int | None = Query(default=None, ge=1, le=12),
    anio: int | None = Query(default=None, ge=2000, le=2100),
    # ?mes=9&anio=2026 → solo los ingresos de ese mes, como en gastos: la
    # pantalla lista mes por mes y ninguna consulta se acerca al tope de 200.
    limite: int = Query(default=50, ge=1, le=200),
    # ?limite=20 → cuántos resultados devolver, entre 1 y 200
    offset: int = Query(default=0, ge=0),
    # ?offset=50 → desde qué posición empezar (para paginación)
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if (mes is None) != (anio is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Para filtrar por mes hay que indicar el mes y el año juntos",
        )

    query = db.query(Ingreso).filter(Ingreso.usuario_id == current_user.id)
    # filtramos siempre por usuario → cada uno solo ve sus propios ingresos

    if mes is not None:
        # Rango [día 1 del mes, día 1 del mes siguiente), en UTC, que es como
        # se guardan y se muestran las fechas.
        desde = datetime(anio, mes, 1, tzinfo=timezone.utc)
        hasta = datetime(anio + (mes == 12), mes % 12 + 1, 1, tzinfo=timezone.utc)
        query = query.filter(Ingreso.fecha >= desde, Ingreso.fecha < hasta)

    if categoria:
        query = query.filter(Ingreso.categoria == categoria)
        # si mandaron ?categoria=X, agregamos ese filtro adicional

    if solo_duplicados:
        query = query.filter(Ingreso.es_duplicado.is_(True))

    ingresos = query.order_by(Ingreso.fecha.desc(), Ingreso.id.desc()).offset(offset).limit(limite).all()
    # order_by fecha descendente → los más recientes primero. El id desempata
    # los del mismo día: sin él, la base podía devolverlos en otro orden en
    # cada pedido y al paginar uno aparecía dos veces y otro nunca.

    return ingresos


# -------------------------------------------------------------------
# GET /ingresos/meses
# Meses con ingresos (para el selector de la pantalla). Va antes de
# /{ingreso_id} para que "meses" no se lea como un id.
# -------------------------------------------------------------------
@router.get("/meses", response_model=list[MesConIngresos])
def listar_meses_con_ingresos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    anio = extract("year", Ingreso.fecha)
    mes = extract("month", Ingreso.fecha)
    filas = (
        db.query(anio.label("anio"), mes.label("mes"),
                 func.count(Ingreso.id), func.sum(Ingreso.monto))
        .filter(Ingreso.usuario_id == current_user.id)
        .group_by(anio, mes)
        .order_by(anio.desc(), mes.desc())
        .all()
    )
    return [
        MesConIngresos(anio=int(a), mes=int(m), cantidad=c, total=float(t or 0))
        for a, m, c, t in filas
    ]


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

    # Antes de tocar nada se anotan los gemelos actuales: si la edición cambia
    # el importe o la fecha, esos registros pueden quedar sin par y hay que
    # retirarles la advertencia.
    gemelos_previos = _buscar_ingresos_gemelos(db, ingreso)

    ingreso.descripcion = datos.descripcion
    ingreso.monto = datos.monto
    ingreso.categoria = datos.categoria
    ingreso.fecha = datos.fecha

    db.commit()
    db.refresh(ingreso)

    cambio_huerfanos = _revisar_huerfanos(db, gemelos_previos)
    cambio_marca = _actualizar_marca_duplicado(db, ingreso)
    if cambio_huerfanos or cambio_marca:
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

    # Al borrar una de las dos cargas repetidas, la que queda deja de ser
    # duplicada: se le retira la advertencia en la misma operación.
    gemelos_previos = _buscar_ingresos_gemelos(db, ingreso)

    db.delete(ingreso)
    db.commit()

    if _revisar_huerfanos(db, gemelos_previos):
        db.commit()
