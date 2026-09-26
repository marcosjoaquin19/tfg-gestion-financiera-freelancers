"""
Servicio de detección de gastos repetidos.

Un gasto registrado dos veces infla los gastos del mes, el resumen y el
reporte PDF. El caso más común es mixto: el usuario anota un pago a mano y
después importa el extracto del banco, donde ese mismo pago aparece con otra
descripción ("DEBITO HOSTING ...") y a veces un día más tarde.

La regla es la del detector de la Auditoría (mismo monto y categoría dentro de
una ventana de días) y la usan las dos vías por las que entra un gasto —la
carga manual (routers/gastos.py) y la importación de extractos
(routers/importar.py)— para que la marca y el filtro "Solo duplicados" se
comporten igual venga el dato de donde venga. Se avisa, no se bloquea.
"""

# PATRÓN: Servicio de dominio — la regla vive en una sola capa y la comparten
# los routers que la necesitan, en lugar de que uno importe del otro.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.gasto import Gasto
from app.services.auditoria import VENTANA_DUPLICADOS_DIAS


def _sin_zona(fecha):
    return fecha.replace(tzinfo=None) if fecha.tzinfo else fecha


def buscar_gastos_gemelos(db: Session, gasto: Gasto) -> list[Gasto]:
    """Otros gastos del mismo usuario con igual monto y categoría dentro de la
    ventana de días. Es la misma regla que usa el detector de la Auditoría."""
    fecha = _sin_zona(gasto.fecha)
    desde = fecha - timedelta(days=VENTANA_DUPLICADOS_DIAS)
    hasta = fecha + timedelta(days=VENTANA_DUPLICADOS_DIAS)

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
    return [g for g in candidatos if desde <= _sin_zona(g.fecha) <= hasta]


def marcar_duplicado_si_corresponde(db: Session, gasto: Gasto) -> bool:
    """Detección inmediata de duplicados al crear, importar o editar un gasto.

    Si hay gemelos, marca AMBOS como duplicados al instante, así aparecen en
    "Solo duplicados" sin ejecutar la auditoría a mano. Si no los hay (por
    ejemplo, porque se le corrigió el importe), le retira la marca.
    Devuelve si cambió algo.
    """
    gemelos = buscar_gastos_gemelos(db, gasto)
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


def revisar_huerfanos(db: Session, antiguos_gemelos: list[Gasto]) -> bool:
    """Desmarca a los que se quedaron sin par tras editar o borrar un gasto.

    Sin este paso, corregir el importe de un duplicado (o borrarlo) dejaba al
    otro gasto advertido para siempre, avisando de un problema que ya no existe.
    """
    hubo_cambios = False
    for anterior in antiguos_gemelos:
        if anterior.es_duplicado and not buscar_gastos_gemelos(db, anterior):
            anterior.es_duplicado = False
            hubo_cambios = True
    return hubo_cambios
