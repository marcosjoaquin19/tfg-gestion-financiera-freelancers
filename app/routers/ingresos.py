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
  GET    /ingresos/      → lista con filtros (categoría, paginación).
  GET    /ingresos/{id}  → devuelve un ingreso.
  PUT    /ingresos/{id}  → edita un ingreso.
  DELETE /ingresos/{id}  → elimina un ingreso.
"""

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


def _normalizar(texto: str) -> str:
    """Deja la descripción comparable: sin mayúsculas ni espacios de más."""
    return " ".join((texto or "").lower().split())


def _dia(fecha):
    """Día calendario de una fecha, sea o no consciente de zona horaria."""
    return (fecha.replace(tzinfo=None) if fecha.tzinfo else fecha).date()


def _buscar_ingresos_gemelos(db: Session, ingreso: Ingreso) -> list[Ingreso]:
    """Otros ingresos que son el mismo cobro cargado de nuevo.

    La regla es deliberadamente más estricta que la de gastos, que considera
    duplicado todo par de igual monto y categoría dentro de una ventana de
    tres días. Acá exigen coincidir las tres cosas:

        mismo importe  +  mismo día calendario  +  misma descripción

    El motivo es el plan de pagos: un cliente que abona en cuotas iguales
    genera ingresos de idéntico monto y descripción en fechas distintas, y
    ésos NO son duplicados. Al exigir el mismo día, las cuotas nunca se
    marcan. El precio de la cautela es dejar pasar alguna carga repetida con
    la descripción escrita distinto; se prefiere ese error antes que alarmar
    sobre cobros legítimos.

    La comparación de descripciones ignora mayúsculas y espacios sobrantes,
    así que "Proyecto Web " y "proyecto web" cuentan como la misma.
    """
    candidatos = (
        db.query(Ingreso)
        .filter(
            Ingreso.usuario_id == ingreso.usuario_id,
            Ingreso.id != ingreso.id,
            Ingreso.monto == ingreso.monto,
        )
        .all()
    )

    dia = _dia(ingreso.fecha)
    descripcion = _normalizar(ingreso.descripcion)

    return [
        otro for otro in candidatos
        if _dia(otro.fecha) == dia and _normalizar(otro.descripcion) == descripcion
    ]


def _actualizar_marca_duplicado(db: Session, ingreso: Ingreso) -> bool:
    """Recalcula la marca del ingreso y la de sus gemelos. Devuelve si cambió algo."""
    gemelos = _buscar_ingresos_gemelos(db, ingreso)
    hubo_cambios = False

    nueva_marca = bool(gemelos)
    if ingreso.es_duplicado != nueva_marca:
        ingreso.es_duplicado = nueva_marca
        hubo_cambios = True

    # Un gemelo tiene, como mínimo, a este ingreso como par.
    for gemelo in gemelos:
        if not gemelo.es_duplicado:
            gemelo.es_duplicado = True
            hubo_cambios = True

    return hubo_cambios


def _revisar_huerfanos(db: Session, antiguos_gemelos: list[Ingreso]) -> bool:
    """Desmarca a los que se quedaron sin par tras editar o borrar un ingreso.

    Sin este paso, corregir el importe de un duplicado dejaba al otro registro
    advertido para siempre, avisando de un problema que ya no existe.
    """
    hubo_cambios = False
    for anterior in antiguos_gemelos:
        if anterior.es_duplicado and not _buscar_ingresos_gemelos(db, anterior):
            anterior.es_duplicado = False
            hubo_cambios = True
    return hubo_cambios


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

    if solo_duplicados:
        query = query.filter(Ingreso.es_duplicado.is_(True))

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
