import os
import time
import logging
from decimal import Decimal
from groq import Groq
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from app.models.cache_clasificacion import CacheClasificacion
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.factura import Factura, EstadoFactura
from app.models.alerta_auditoria import AlertaAuditoria
from app.models.proyeccion import Proyeccion

logger = logging.getLogger(__name__)

CATEGORIAS = [
    "Software", "Hardware", "Infraestructura", "Marketing", "Servicios",
    "Capacitación", "Suscripciones", "Transporte", "Alimentación",
    "Impuestos", "Monotributo", "Otros",
]

PROMPT_TEMPLATE = """Eres un asistente contable para freelancers.
Dado el siguiente gasto, devolvé ÚNICAMENTE el nombre de la categoría más apropiada, sin explicación adicional.

Categorías posibles: {categorias}

Descripción del gasto: "{descripcion}"

Categoría:"""

MAX_INTENTOS = 3
ESPERA_RATE_LIMIT = 20


def _es_rate_limit(error: Exception) -> bool:
    mensaje = str(error).lower()
    return "quota" in mensaje or "429" in mensaje


def _llamar_groq(descripcion: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Otros"

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)

    prompt = PROMPT_TEMPLATE.format(
        categorias=", ".join(CATEGORIAS),
        descripcion=descripcion,
    )

    ultimo_error = None
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0,
            )
            categoria = response.choices[0].message.content.strip()

            if categoria in CATEGORIAS:
                return categoria
            for c in CATEGORIAS:
                if c.lower() in categoria.lower():
                    return c
            return "Otros"

        except Exception as e:
            print(f"ERROR GROQ DETALLADO: {type(e).__name__}: {e}")
            ultimo_error = e
            if _es_rate_limit(e) and intento < MAX_INTENTOS:
                logger.warning(f"Rate limit Groq (intento {intento}/{MAX_INTENTOS}), reintentando en {ESPERA_RATE_LIMIT}s...")
                time.sleep(ESPERA_RATE_LIMIT)
            else:
                break

    logger.error(f"Error Groq clasificar_gasto: {ultimo_error}")
    return "Otros"


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


def generar_resumen_financiero(usuario_id: int, db: Session, mes: int, anio: int) -> tuple[str, bool]:
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
                                 total_gastos, cant_facturas_pend, total_facturas_pend), False

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
        return resumen, True

    except Exception as e:
        logger.error(f"Error Groq generar_resumen_financiero: {e}")
        return _fallback_resumen(mes, anio, total_ingresos, cant_ingresos,
                                 total_gastos, cant_facturas_pend, total_facturas_pend), False


def _recomendaciones_fallback(alertas, facturas_pend, facturas_venc, aumentos) -> list[str]:
    recs = []
    if alertas:
        recs.append(f"Tenés {len(alertas)} alerta(s) de auditoría sin resolver. Revisalas para evitar problemas contables.")
    if facturas_venc:
        total = sum(f.monto for f in facturas_venc)
        recs.append(f"Tenés {len(facturas_venc)} factura(s) vencida(s) por ${total:.2f}. Contactá a tus clientes para gestionar el cobro.")
    if facturas_pend:
        total = sum(f.monto for f in facturas_pend)
        recs.append(f"Hay {len(facturas_pend)} factura(s) pendiente(s) por ${total:.2f}. Hacé seguimiento para mantener tu flujo de caja.")
    for cat, pct in aumentos:
        recs.append(f"Tus gastos en {cat} aumentaron un {pct:.0f}% respecto al mes anterior. Revisá si es un gasto recurrente necesario.")
    if not recs:
        recs.append("Tu situación financiera parece estable. Seguí registrando tus ingresos y gastos para mantener un buen control.")
    return recs[:5]


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

    # Proyecciones próximos 30 días
    proyecciones = db.query(Proyeccion).filter(
        Proyeccion.usuario_id == usuario_id,
    ).order_by(Proyeccion.fecha_proyeccion).limit(30).all()
    total_proyectado = sum(p.monto_proyectado for p in proyecciones) or Decimal("0")

    # Armar contexto para el prompt
    alertas_txt = "\n".join(f"- [{a.tipo.value}] {a.descripcion}" for a in alertas) or "Ninguna"
    fact_pend_txt = f"{len(facturas_pend)} factura(s) pendientes por ${sum(f.monto for f in facturas_pend) or 0:.2f}"
    fact_venc_txt = f"{len(facturas_venc)} factura(s) vencidas por ${sum(f.monto for f in facturas_venc) or 0:.2f}"
    aumentos_txt = "\n".join(f"- {cat}: +{pct:.0f}%" for cat, pct in aumentos) or "Ningún aumento significativo"
    proyeccion_txt = f"${total_proyectado:.2f} proyectados en los próximos 30 días" if proyecciones else "Sin proyecciones disponibles"

    prompt = f"""Eres un asesor financiero para freelancers.
Basándote en los datos financieros del usuario, generá entre 3 y 5 recomendaciones concretas y accionables en español.
Cada recomendación debe ser una oración clara y directa. Devolvé SOLO las recomendaciones, una por línea, sin numeración ni viñetas.

Alertas de auditoría sin resolver:
{alertas_txt}

Facturas: {fact_pend_txt} | {fact_venc_txt}

Aumentos de gastos vs mes anterior:
{aumentos_txt}

Proyección de ingresos: {proyeccion_txt}"""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "recomendaciones": _recomendaciones_fallback(alertas, facturas_pend, facturas_venc, aumentos),
            "generado_con_ia": False,
        }

    try:
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.6,
        )
        texto = response.choices[0].message.content.strip()
        recomendaciones = [r.strip() for r in texto.splitlines() if r.strip()][:5]
        return {"recomendaciones": recomendaciones, "generado_con_ia": True}

    except Exception as e:
        logger.error(f"Error Groq generar_recomendaciones: {e}")
        return {
            "recomendaciones": _recomendaciones_fallback(alertas, facturas_pend, facturas_venc, aumentos),
            "generado_con_ia": False,
        }


def clasificar_gasto(descripcion: str, db: Session) -> str:
    descripcion_normalizada = descripcion.strip().lower()

    cached = db.query(CacheClasificacion).filter(
        CacheClasificacion.descripcion_normalizada == descripcion_normalizada
    ).first()

    if cached:
        return cached.categoria

    categoria = _llamar_groq(descripcion)

    entrada = CacheClasificacion(
        descripcion_normalizada=descripcion_normalizada,
        categoria=categoria,
    )
    db.add(entrada)
    db.commit()

    return categoria
