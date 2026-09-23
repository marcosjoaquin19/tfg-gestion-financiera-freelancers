"""
Servicio de detección de ingresos repetidos.

Un ingreso cargado dos veces infla la facturación de los últimos doce meses y
puede hacer que el semáforo del Monotributo anuncie un cambio de categoría que
no corresponde. Este módulo concentra la regla que decide cuándo dos ingresos
son la misma cobranza.

Lo usan las dos vías por las que entra un ingreso —la carga manual
(routers/ingresos.py) y la importación de extractos (routers/importar.py)—
para que la marca y el filtro "Solo duplicados" se comporten igual venga el
dato de donde venga.

Los gastos no pasan por acá: tienen su propia detección inmediata en su router
y, además, el detector del módulo de Auditoría.
"""

# PATRÓN: Servicio de dominio — la regla vive en una sola capa y la comparten
# los routers que la necesitan, en lugar de que uno importe del otro.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md

from sqlalchemy.orm import Session

from app.models.ingreso import Ingreso


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
