import os
import logging
from decimal import Decimal
from groq import Groq
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.factura import Factura, EstadoFactura
from app.models.alerta_auditoria import AlertaAuditoria
from app.models.proyeccion import Proyeccion

logger = logging.getLogger(__name__)

# Categorías cerradas válidas para clasificación de gastos.
# Se mantienen acá para los fallbacks locales y para validar respuestas agregadas.
CATEGORIAS = [
    "Software", "Hardware", "Infraestructura", "Marketing", "Servicios",
    "Capacitación", "Suscripciones", "Transporte", "Alimentación",
    "Impuestos", "Monotributo", "Otros",
]


MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _fallback_resumen(mes: int, anio: int, total_ingresos: Decimal, cant_ingresos: int,
                      total_gastos: Decimal, cant_facturas_pend: int, total_facturas_pend: Decimal) -> str:
    return (
        f"En {MESES_ES[mes]} {anio} registraste {cant_ingresos} ingreso(s) por ${total_ingresos:.2f}. "
        f"Tus gastos fueron ${total_gastos:.2f}. "
        f"Tenés {cant_facturas_pend} factura(s) pendiente(s) por ${total_facturas_pend:.2f}."
    )


def generar_resumen_financiero(usuario_id: int, db: Session, mes: int, anio: int) -> tuple[str, bool, bool]:
    """Devuelve (texto, generado_con_ia, sin_datos)."""
    # Ingresos del mes
    ingresos = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id,
        extract("month", Ingreso.fecha) == mes,
        extract("year", Ingreso.fecha) == anio,
    ).all()
    total_ingresos = sum(i.monto for i in ingresos) or Decimal("0")
    cant_ingresos = len(ingresos)

    # Gastos del mes agrupados por categoría
    gastos_por_categoria = db.query(
        Gasto.categoria,
        func.sum(Gasto.monto).label("total"),
    ).filter(
        Gasto.usuario_id == usuario_id,
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).group_by(Gasto.categoria).all()
    total_gastos = sum(r.total for r in gastos_por_categoria) or Decimal("0")

    # Facturas pendientes
    facturas_pendientes = db.query(Factura).filter(
        Factura.usuario_id == usuario_id,
        Factura.estado == EstadoFactura.PENDIENTE,
    ).all()
    cant_facturas_pend = len(facturas_pendientes)
    total_facturas_pend = sum(f.monto for f in facturas_pendientes) or Decimal("0")

    # Mes sin actividad: no tiene sentido invocar la IA (devolvía textos raros
    # mezclando facturas pendientes de otros meses). Mostramos un mensaje claro.
    if cant_ingresos == 0 and total_gastos == 0:
        mensaje = (
            f"No registramos ingresos ni gastos en {MESES_ES[mes]} {anio}. "
            f"Cuando cargues movimientos de este mes, vas a ver acá el resumen de tu situación financiera."
        )
        return mensaje, False, True

    # Armar contexto para el prompt
    detalle_gastos = ", ".join(
        f"{r.categoria}: ${r.total:.2f}" for r in gastos_por_categoria
    ) or "sin gastos registrados"

    prompt = f"""Eres un asistente financiero para freelancers.
Generá un resumen financiero en español, en lenguaje natural, amigable y conciso. Máximo 150 palabras.

Datos de {MESES_ES[mes]} {anio}:
- Ingresos: {cant_ingresos} ingreso(s) por un total de ${total_ingresos:.2f}
- Gastos por categoría: {detalle_gastos}
- Total gastos: ${total_gastos:.2f}
- Facturas pendientes de cobro: {cant_facturas_pend} por ${total_facturas_pend:.2f}
- Balance del mes: ${total_ingresos - total_gastos:.2f}

Resumí la situación financiera destacando los puntos más relevantes."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback_resumen(mes, anio, total_ingresos, cant_ingresos,
                                 total_gastos, cant_facturas_pend, total_facturas_pend), False, False

    try:
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7,
        )
        resumen = response.choices[0].message.content.strip()
        return resumen, True, False

    except Exception as e:
        logger.error(f"Error Groq generar_resumen_financiero: {e}")
        return _fallback_resumen(mes, anio, total_ingresos, cant_ingresos,
                                 total_gastos, cant_facturas_pend, total_facturas_pend), False, False


AHORRO_PCT_MIN = 0.10  # meta sana de ahorro: 10%–20% de los ingresos (regla 50/30/20)
AHORRO_PCT_MAX = 0.20


def generar_recomendaciones(usuario_id: int, db: Session) -> dict:
    from datetime import datetime
    hoy = datetime.now()
    mes_actual = hoy.month
    anio_actual = hoy.year
    mes_anterior = mes_actual - 1 if mes_actual > 1 else 12
    anio_anterior = anio_actual if mes_actual > 1 else anio_actual - 1

    # Alertas no resueltas
    alertas = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == usuario_id,
        AlertaAuditoria.resuelta == False,
    ).all()

    # Facturas pendientes y vencidas
    facturas_pend = db.query(Factura).filter(
        Factura.usuario_id == usuario_id,
        Factura.estado == EstadoFactura.PENDIENTE,
    ).all()
    facturas_venc = db.query(Factura).filter(
        Factura.usuario_id == usuario_id,
        Factura.estado == EstadoFactura.VENCIDA,
    ).all()

    # Gastos mes actual vs mes anterior por categoría
    def gastos_por_cat(mes, anio):
        rows = db.query(
            Gasto.categoria,
            func.sum(Gasto.monto).label("total"),
        ).filter(
            Gasto.usuario_id == usuario_id,
            extract("month", Gasto.fecha) == mes,
            extract("year", Gasto.fecha) == anio,
        ).group_by(Gasto.categoria).all()
        return {r.categoria: r.total for r in rows}

    gastos_actual = gastos_por_cat(mes_actual, anio_actual)
    gastos_anterior = gastos_por_cat(mes_anterior, anio_anterior)

    aumentos = []
    for cat, total_actual in gastos_actual.items():
        total_prev = gastos_anterior.get(cat, Decimal("0"))
        if total_prev > 0:
            pct = float((total_actual - total_prev) / total_prev * 100)
            if pct >= 30:
                aumentos.append((cat, pct))
    aumentos.sort(key=lambda x: x[1], reverse=True)

    # Superávit promedio mensual (ventana de 6 meses) para el consejo de ahorro.
    from datetime import timedelta
    from app.services.formato import formato_pesos_ar
    desde = hoy - timedelta(days=180)
    ingresos_win = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id, Ingreso.fecha >= desde,
    ).all()
    gastos_win = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id, Gasto.fecha >= desde,
    ).all()
    meses_set = (
        {(i.fecha.year, i.fecha.month) for i in ingresos_win}
        | {(g.fecha.year, g.fecha.month) for g in gastos_win}
    )
    n_meses = max(len(meses_set), 1)
    prom_ing = float(sum(i.monto for i in ingresos_win) or 0) / n_meses
    prom_gas = float(sum(g.monto for g in gastos_win) or 0) / n_meses
    superavit = prom_ing - prom_gas

    # Recomendaciones determinísticas (sin IA): reglas sobre los datos. Estables,
    # reproducibles y dinámicas (desaparecen cuando el problema se resuelve).
    # Cada situación genera su propia recomendación, ordenadas por urgencia.
    recs: list[str] = []

    if facturas_venc:
        total = sum(f.monto for f in facturas_venc)
        recs.append(
            f"Tenés {len(facturas_venc)} factura(s) vencida(s) por {formato_pesos_ar(total)} sin cobrar. "
            f"Contactá a esos clientes: es plata que ya deberías haber recibido."
        )
    if alertas:
        recs.append(
            f"Tenés {len(alertas)} alerta(s) de auditoría sin resolver. "
            f"Revisalas en la sección Auditoría para mantener tus datos sanos."
        )
    if facturas_pend:
        total = sum(f.monto for f in facturas_pend)
        recs.append(
            f"Tenés {len(facturas_pend)} factura(s) pendiente(s) de cobro por {formato_pesos_ar(total)}. "
            f"Hacé seguimiento para no cortar tu flujo de caja."
        )

    # Picos de gasto: valor agregado, no se ve en otro módulo.
    for cat, pct in aumentos[:2]:
        recs.append(
            f"Tus gastos en {cat} subieron {pct:.0f}% respecto al mes anterior. "
            f"Revisá si es un gasto necesario o si podés recortarlo."
        )

    # (3) Consejo de ahorro: SIEMPRE presente cuando hay ingresos. Dos casos.
    if prom_ing > 0:
        ahorro_min = prom_ing * AHORRO_PCT_MIN
        ahorro_max = prom_ing * AHORRO_PCT_MAX
        rango_pct = f"{int(AHORRO_PCT_MIN * 100)}%–{int(AHORRO_PCT_MAX * 100)}%"
        if superavit > 0:
            recs.append(
                f"Este período te quedó superávit ({formato_pesos_ar(superavit)} por mes: cobrás más de lo que gastás). "
                f"Aprovechalo y destiná entre el {rango_pct} de tus ingresos "
                f"({formato_pesos_ar(ahorro_min)} a {formato_pesos_ar(ahorro_max)} por mes) a un fondo de reserva "
                f"o una inversión conservadora como un plazo fijo."
            )
        else:
            recs.append(
                f"⚠️ No te quedó superávit: en promedio gastás tanto o más de lo que ingresás "
                f"(déficit de {formato_pesos_ar(abs(superavit))} por mes). Ajustá tus gastos y apuntá a ahorrar al menos "
                f"el {rango_pct} de lo que generás cada mes ({formato_pesos_ar(ahorro_min)} a {formato_pesos_ar(ahorro_max)})."
            )

    if not recs:
        recs.append(
            "Tu situación financiera está en orden: sin pendientes y con los gastos controlados. "
            "Seguí registrando tus movimientos para mantener el control."
        )

    return {"recomendaciones": recs, "generado_con_ia": False}


UMBRAL_CONFIANZA_ML = 0.30
# El SVM lineal no devuelve probabilidades nativas: la confianza se deriva de
# la brecha entre el mejor y el segundo mejor margen de decision_function(),
# mapeada a [0, 1) con 1 - e^(-brecha) (ver ml_service._confianza_svm). Vale 0
# ante un empate (dos categorías compiten cabeza a cabeza) y tiende a 1 cuando
# hay una clase claramente dominante. Por debajo de 0.30 (brecha < ~0.36) el
# modelo está dudando y la predicción se marca para revisión del usuario; para
# Naive Bayes se usa directamente la probabilidad de predict_proba.


def clasificar_gasto(descripcion: str, db: Session, usuario_id: int = 0) -> dict:
    """Clasifica un gasto usando exclusivamente el modelo ML local.

    Orden de resolución:

    1. Si el usuario YA corrigió explícitamente esta misma descripción
       (entrada en cache_clasificacion con su usuario_id), devolver la
       corrección directamente con confianza 1.0. Es ground truth aportado
       por el dueño de los datos: no hay nada que predecir.

    2. Si no hay corrección previa, invocar el clasificador NLP local.

    3. Si la confianza del ML está por debajo del umbral, sugerir "Otros"
       y marcar para revisión manual (HU-04).

    Política de soberanía de datos del TFG: la descripción del gasto NUNCA se
    envía a servicios externos. Las correcciones del usuario alimentan los
    futuros reentrenamientos y además sirven de atajo en el paso 1.
    """
    from app.services import ml_service
    from app.models.cache_clasificacion import CacheClasificacion

    # Paso 1: lookup de corrección explícita previa del usuario. La
    # normalización es la misma que usa registrar_ejemplo al persistir
    # (NFKD + sin tildes + colapso de espacios + lowercase + strip), así
    # variaciones tipográficas (mayúsculas, espacios extra) matchean igual.
    descripcion_norm = ml_service.normalizar_descripcion(descripcion)
    correccion = db.query(CacheClasificacion).filter(
        CacheClasificacion.usuario_id == usuario_id,
        CacheClasificacion.descripcion_normalizada == descripcion_norm,
    ).first()
    if correccion is not None:
        return {
            "categoria_sugerida": correccion.categoria,
            "fuente": "correccion_usuario",
            "confianza": 1.0,
            "requiere_revision": False,
        }

    # Paso 2 y 3: clasificador ML local + umbral de revisión.
    try:
        resultado_ml = ml_service.clasificar_gasto(descripcion, db, usuario_id)
        if resultado_ml["confianza"] >= UMBRAL_CONFIANZA_ML:
            # Ya no registramos la predicción del modelo como "ejemplo": el
            # reentrenamiento se alimenta de gastos reales (creados o
            # corregidos por el usuario), no de las propias predicciones del
            # clasificador. Persistir las predicciones inflaría la señal y
            # reforzaría el sesgo del modelo en lugar de corregirlo.
            return {
                "categoria_sugerida": resultado_ml["categoria"],
                "fuente": "ml_propio",
                "confianza": resultado_ml["confianza"],
                "requiere_revision": False,
            }
        # Confianza insuficiente: no asumimos categoría, devolvemos "Otros"
        # como placeholder y delegamos al usuario la corrección.
        return {
            "categoria_sugerida": "Otros",
            "fuente": "ml_propio",
            "confianza": resultado_ml["confianza"],
            "requiere_revision": True,
        }
    except Exception as e:
        logger.error(f"Error ML clasificar_gasto usuario {usuario_id}: {e}")
        return {
            "categoria_sugerida": "Otros",
            "fuente": "ml_propio",
            "confianza": 0.0,
            "requiere_revision": True,
        }
