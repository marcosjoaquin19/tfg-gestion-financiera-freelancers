"""
Router de Gastos — registro y consulta de gastos.

Expone el CRUD de gastos bajo /gastos. Al crear un gasto, si no se indica
categoría se la asigna automáticamente el clasificador de ML, y se detectan
duplicados al instante (mismo monto/categoría dentro de una ventana de días);
editar o borrar un gasto recalcula esa marca.

Endpoints:
  POST   /gastos/      → crea un gasto (clasificación automática + chequeo de duplicados).
  GET    /gastos/      → lista con filtros (mes, categoría, solo duplicados, etc.).
  GET    /gastos/meses → meses con gastos cargados (para el selector de la pantalla).
  GET    /gastos/{id}  → devuelve un gasto.
  PUT    /gastos/{id}  → edita un gasto.
  DELETE /gastos/{id}  → elimina un gasto.
"""

import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import SessionLocal, get_db
from app.models.usuario import Usuario
from app.models.gasto import Gasto
from app.schemas.gasto import GastoCreate, GastoResponse
from app.dependencies import get_current_user
from app.services.ia_service import clasificar_gasto
from app.services.auditoria import VENTANA_DUPLICADOS_DIAS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gastos", tags=["Gastos"])


def _buscar_gastos_gemelos(db: Session, gasto: Gasto) -> list[Gasto]:
    """Otros gastos del mismo usuario con igual monto y categoría dentro de la
    ventana de días. Es la misma regla que usa el detector de la Auditoría."""
    fecha = gasto.fecha
    fecha_naive = fecha.replace(tzinfo=None) if fecha.tzinfo else fecha
    desde = fecha_naive - timedelta(days=VENTANA_DUPLICADOS_DIAS)
    hasta = fecha_naive + timedelta(days=VENTANA_DUPLICADOS_DIAS)

    candidatos = (
        db.query(Gasto)
        .filter(
            Gasto.usuario_id == gasto.usuario_id,
            Gasto.id != gasto.id,
            Gasto.monto == gasto.monto,
            Gasto.categoria == gasto.categoria,
        )
        .all()
    )

    return [
        g for g in candidatos
        if desde <= (g.fecha.replace(tzinfo=None) if g.fecha.tzinfo else g.fecha) <= hasta
    ]


def _marcar_duplicado_si_corresponde(db: Session, gasto: Gasto) -> bool:
    """Detección inmediata de duplicados al crear o editar un gasto.

    Si hay gemelos, marca AMBOS como duplicados al instante, así aparecen en
    "Solo duplicados" sin ejecutar la auditoría a mano. Si no los hay (por
    ejemplo, porque se le corrigió el importe), le retira la marca.
    Devuelve si cambió algo.
    """
    gemelos = _buscar_gastos_gemelos(db, gasto)
    hubo_cambios = False

    nueva_marca = bool(gemelos)
    if gasto.es_duplicado != nueva_marca:
        gasto.es_duplicado = nueva_marca
        hubo_cambios = True

    for g in gemelos:
        if not g.es_duplicado:
            g.es_duplicado = True
            hubo_cambios = True
    return hubo_cambios


def _revisar_huerfanos(db: Session, antiguos_gemelos: list[Gasto]) -> bool:
    """Desmarca a los que se quedaron sin par tras editar o borrar un gasto.

    Sin este paso, corregir el importe de un duplicado (o borrarlo) dejaba al
    otro gasto advertido para siempre, avisando de un problema que ya no existe.
    """
    hubo_cambios = False
    for anterior in antiguos_gemelos:
        if anterior.es_duplicado and not _buscar_gastos_gemelos(db, anterior):
            anterior.es_duplicado = False
            hubo_cambios = True
    return hubo_cambios


def _reentrenar_en_background(usuario_id: int, motivo: str) -> None:
    """Tarea asíncrona que evalúa y dispara el reentrenamiento del modelo.

    La sesión de BD del request se cierra apenas FastAPI termina la respuesta,
    así que para una tarea diferida hay que abrir una sesión nueva. Si algo
    falla acá, se loguea pero no afecta al usuario: el gasto ya quedó guardado.
    """
    from app.services import ml_service

    db = SessionLocal()
    try:
        resultado = ml_service.evaluar_reentrenamiento_automatico(db, usuario_id, motivo)
        if resultado.get("reentrenado"):
            logger.info(
                f"Reentrenamiento automático usuario {usuario_id}: {resultado.get('razon')} "
                f"(precision={resultado.get('precision')}, n={resultado.get('n_ejemplos')})"
            )
    except Exception as e:
        logger.error(f"Falló reentrenamiento automático usuario {usuario_id}: {e}")
    finally:
        db.close()


class ClasificarRequest(BaseModel):
    descripcion: str


class ClasificarResponse(BaseModel):
    categoria_sugerida: str
    fuente: str | None = None
    confianza: float | None = None
    requiere_revision: bool = False


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
        requiere_revision=resultado.get("requiere_revision", False),
    )


@router.post("/", response_model=GastoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto(
    datos: GastoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Si el cliente no manda categoría, la infiere el clasificador local (HU-04).
    # Debajo del umbral de confianza, clasificar_gasto() ya devuelve "Otros",
    # que es el comportamiento esperado para una descripción sin señal clara.
    categoria = datos.categoria
    if categoria is None:
        categoria = clasificar_gasto(datos.descripcion, db, current_user.id)["categoria_sugerida"]

    nuevo_gasto = Gasto(
        usuario_id=current_user.id,
        descripcion=datos.descripcion,
        monto=datos.monto,
        categoria=categoria,
        fecha=datos.fecha,
        # es_duplicado arranca en False, el módulo de auditoría lo puede marcar después
    )
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)

    # Marca duplicados al instante (mismo monto+categoría dentro de la ventana),
    # para que se reflejen en "Solo duplicados" sin correr la auditoría a mano.
    if _marcar_duplicado_si_corresponde(db, nuevo_gasto):
        db.commit()
        db.refresh(nuevo_gasto)

    # Aprende de a poco: cada N gastos nuevos, reentrenamos el modelo del
    # usuario en background. La política está en ml_service.
    background_tasks.add_task(_reentrenar_en_background, current_user.id, "creacion")

    return nuevo_gasto


class MesConGastos(BaseModel):
    anio: int
    mes: int
    cantidad: int
    total: float


@router.get("/meses", response_model=list[MesConGastos])
def listar_meses_con_gastos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Meses en los que el usuario tiene gastos, del más reciente al más viejo.

    Alimenta el selector de mes de la pantalla: así solo se ofrecen meses con
    datos y cada opción muestra cuántos gastos tiene.
    """
    anio = extract("year", Gasto.fecha)
    mes = extract("month", Gasto.fecha)
    filas = (
        db.query(anio.label("anio"), mes.label("mes"),
                 func.count(Gasto.id), func.sum(Gasto.monto))
        .filter(Gasto.usuario_id == current_user.id)
        .group_by(anio, mes)
        .order_by(anio.desc(), mes.desc())
        .all()
    )
    return [
        MesConGastos(anio=int(a), mes=int(m), cantidad=c, total=float(t or 0))
        for a, m, c, t in filas
    ]


@router.get("/", response_model=list[GastoResponse])
def listar_gastos(
    categoria: str | None = Query(default=None),
    solo_duplicados: bool = Query(default=False),
    # ?solo_duplicados=true → filtra solo los gastos marcados como duplicados por auditoría
    mes: int | None = Query(default=None, ge=1, le=12),
    anio: int | None = Query(default=None, ge=2000, le=2100),
    # ?mes=9&anio=2026 → solo los gastos de ese mes. La pantalla lista mes por
    # mes: un mes nunca se acerca al tope de 200 filas, mientras que la lista
    # completa de un usuario con varios meses de uso sí lo supera.
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if (mes is None) != (anio is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Para filtrar por mes hay que indicar el mes y el año juntos",
        )

    query = db.query(Gasto).filter(Gasto.usuario_id == current_user.id)

    if mes is not None:
        # Rango [día 1 del mes, día 1 del mes siguiente), en UTC, que es como
        # se guardan y se muestran las fechas.
        desde = datetime(anio, mes, 1, tzinfo=timezone.utc)
        hasta = datetime(anio + (mes == 12), mes % 12 + 1, 1, tzinfo=timezone.utc)
        query = query.filter(Gasto.fecha >= desde, Gasto.fecha < hasta)

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    gasto = db.query(Gasto).filter(
        Gasto.id == gasto_id,
        Gasto.usuario_id == current_user.id,
    ).first()

    if not gasto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado")

    # Capturamos la categoría previa antes de pisarla. Si cambió, sabemos que
    # el usuario está corrigiendo una clasificación — esa es la señal más
    # valiosa para reentrenar.
    categoria_anterior = gasto.categoria
    gemelos_anteriores = _buscar_gastos_gemelos(db, gasto)

    gasto.descripcion = datos.descripcion
    gasto.monto = datos.monto
    # Si la edición no trae categoría se conserva la actual: la columna no
    # admite vacío (antes esto terminaba en error 500) y reclasificar en
    # silencio podría pisar una categoría que el usuario ya había corregido.
    if datos.categoria is not None:
        gasto.categoria = datos.categoria
    gasto.fecha = datos.fecha
    db.flush()
    # Releemos para comparar con el monto ya redondeado a 2 decimales por la
    # base, igual que al crear.
    db.refresh(gasto)

    # El cambio puede crear un par nuevo o deshacer el anterior.
    _marcar_duplicado_si_corresponde(db, gasto)
    _revisar_huerfanos(db, gemelos_anteriores)

    db.commit()
    db.refresh(gasto)

    if categoria_anterior != gasto.categoria:
        background_tasks.add_task(_reentrenar_en_background, current_user.id, "correccion")

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

    # Si era la mitad de un par duplicado, el otro gasto deja de serlo.
    gemelos = _buscar_gastos_gemelos(db, gasto)
    db.delete(gasto)
    db.flush()
    _revisar_huerfanos(db, gemelos)
    db.commit()
