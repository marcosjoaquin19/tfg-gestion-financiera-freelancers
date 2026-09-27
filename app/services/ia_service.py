"""
Servicio de IA — resumen financiero y clasificación de gastos.

Reúne:
  - generar_resumen_financiero(): arma un resumen mensual en lenguaje natural
    usando el modelo de Groq. Por privacidad, a la IA solo se le envían datos
    numéricos agregados, nunca descripciones libres del usuario. La respuesta
    se controla (formato, largo, cifras) antes de mostrarla; si no pasa o si
    Groq no responde, se usa una plantilla local.
También expone clasificar_gasto(), usado al crear gastos.
"""

# PATRÓN: Facade — punto único de entrada a clasificación y resumen (las recomendaciones, que no usan IA, viven en recomendaciones_service).
# PATRÓN: Cache-Aside — clasificar_gasto() consulta la corrección del usuario antes de invocar el modelo.
# PATRÓN: Chain of Responsibility — corrección explícita → modelo ML → 'Otros' + revisión manual.
# PATRÓN: Fallback determinístico — si no hay API de IA disponible, el resumen se arma con reglas locales.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md

import os
import re
import logging
from decimal import Decimal
from typing import NamedTuple

import httpx
from groq import Groq, RateLimitError
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.factura import Factura, EstadoFactura
from app.models.alerta_auditoria import AlertaAuditoria

from app.services.categorias_gasto import CATEGORIAS_GASTO
from app.services.facturas_estado import marcar_vencidas
from app.services.formato import formato_pesos_ar

logger = logging.getLogger(__name__)

# Categorías cerradas válidas para clasificación de gastos.
# La lista vive en categorias_gasto; este alias la usan los fallbacks locales.
CATEGORIAS = CATEGORIAS_GASTO


MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


# -------------------------------------------------------------------
# RESUMEN FINANCIERO (HU-11)
# -------------------------------------------------------------------
# Flujo: se calculan los totales del mes → se le piden a Groq en un prompt con
# reglas estrictas → la respuesta pasa por controles (formato, largo, cifras)
# → si no los pasa se reintenta una vez → si tampoco, o si Groq no responde,
# se usa la plantilla local. Nunca se muestra como "IA" un texto que no pasó
# los controles.

GROQ_MODELO_POR_DEFECTO = "openai/gpt-oss-120b"

GROQ_TIMEOUT = httpx.Timeout(10.0, connect=3.0)
GROQ_REINTENTOS_RED = 0
# 10 s para responder y 3 s para conectar, sin reintentos de red: sin conexión,
# la plantilla aparece en ~3 s. Con los valores por defecto de la librería
# (60 s y 2 reintentos) tardaba 16 s, y con una red lenta podía tardar minutos.

GROQ_MAX_TOKENS = 700
# gpt-oss "razona" antes de escribir y ese razonamiento cuenta dentro del
# límite de tokens. Con 250, 4 de cada 10 resúmenes llegaban cortados.

GROQ_TEMPERATURA = 0.3
# Baja: el resumen tiene que ser fiel a los datos, no creativo. Con 0,7 el
# texto variaba mucho entre un pedido y otro y agregaba afirmaciones propias.

MAX_PALABRAS_RESUMEN = 150      # criterio de aceptación de HU-11
MIN_PALABRAS_RESUMEN = 40       # por debajo no es un resumen: se descarta
INTENTOS_IA = 2                 # un reintento si la respuesta no pasa los controles

INSTRUCCIONES_RESUMEN = """Sos un asistente financiero para freelancers monotributistas de Argentina.
Redactá un resumen del mes a partir de los datos que te paso. Reglas obligatorias:
1. Escribí en español rioplatense, tratando al usuario de vos (tenés, cobraste, gastaste), en un tono cercano y profesional.
2. Un único párrafo de texto plano, de 3 a 5 oraciones y entre 60 y 120 palabras: sin títulos, sin viñetas, sin negritas ni ningún otro formato.
3. Usá solamente las cifras de los datos, copiadas exactamente como están escritas. No calcules cifras nuevas (sumas, restas, porcentajes, promedios) ni hagas proyecciones o predicciones sobre meses futuros.
4. No enumeres todas las categorías de gasto: nombrá solo las dos o tres de mayor monto.
5. Hablá de ingresos o cobros; no menciones trabajos, clientes ni proyectos.
6. Las facturas pendientes son las que están sin cobrar hoy y pueden ser de otros meses: no las presentes como parte del mes.
7. Podés cerrar con una observación breve que se desprenda de los datos (por ejemplo, si el balance fue positivo o negativo, o que conviene hacer seguimiento de las facturas pendientes), sin cifras nuevas.
8. No agregues información que no esté en los datos."""


class ResultadoResumen(NamedTuple):
    texto: str
    generado_con_ia: bool
    sin_datos: bool
    motivo_reserva: str | None = None
    # por qué se usó la plantilla local: "sin_clave" (no hay API key
    # configurada), "limite_de_uso" (Groq respondió 429: se superó la cuota
    # por minuto del plan), "servicio_no_disponible" (error, timeout o sin
    # red) o "respuesta_descartada" (la IA respondió, pero el texto no pasó
    # los controles dos veces). None cuando el texto es de la IA.


class DatosMes(NamedTuple):
    mes: int
    anio: int
    total_ingresos: Decimal
    cant_ingresos: int
    gastos_por_categoria: list          # [(categoria, total)], de mayor a menor
    total_gastos: Decimal
    cant_facturas_pend: int
    total_facturas_pend: Decimal

    @property
    def balance(self) -> Decimal:
        return self.total_ingresos - self.total_gastos

    @property
    def periodo(self) -> str:
        return f"{MESES_ES[self.mes]} {self.anio}"


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _texto_balance(balance: Decimal) -> str:
    if balance > 0:
        return f"superávit de {formato_pesos_ar(balance)}"
    if balance < 0:
        return f"déficit de {formato_pesos_ar(-balance)}"
    return "equilibrio: ingresos y gastos iguales"


def _datos_del_mes(db: Session, usuario_id: int, mes: int, anio: int) -> DatosMes:
    ingresos = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id,
        extract("month", Ingreso.fecha) == mes,
        extract("year", Ingreso.fecha) == anio,
    ).all()

    gastos = db.query(
        Gasto.categoria,
        func.sum(Gasto.monto).label("total"),
    ).filter(
        Gasto.usuario_id == usuario_id,
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).group_by(Gasto.categoria).all()
    gastos_por_categoria = sorted(
        ((r.categoria, Decimal(r.total)) for r in gastos), key=lambda x: x[1], reverse=True,
    )

    # Facturas pendientes A HOY (las vencidas se marcan antes para no contarlas
    # acá). No son "del mes": se informan así en el prompt y en la plantilla.
    marcar_vencidas(db, usuario_id)
    facturas_pendientes = db.query(Factura).filter(
        Factura.usuario_id == usuario_id,
        Factura.estado == EstadoFactura.PENDIENTE,
    ).all()

    return DatosMes(
        mes=mes,
        anio=anio,
        total_ingresos=Decimal(sum(i.monto for i in ingresos) or 0),
        cant_ingresos=len(ingresos),
        gastos_por_categoria=gastos_por_categoria,
        total_gastos=Decimal(sum(t for _, t in gastos_por_categoria) or 0),
        cant_facturas_pend=len(facturas_pendientes),
        total_facturas_pend=Decimal(sum(f.monto for f in facturas_pendientes) or 0),
    )


def _datos_para_ia(d: DatosMes) -> str:
    """Lo único que viaja a Groq: totales agregados, con los montos ya escritos
    en formato argentino para que el texto use el mismo que el resto de la app.
    Las categorías son las de la lista cerrada, nunca texto del usuario."""
    if d.gastos_por_categoria:
        gastos = "; ".join(f"{cat} {formato_pesos_ar(total)}" for cat, total in d.gastos_por_categoria)
    else:
        gastos = "no hubo gastos"
    if d.cant_facturas_pend:
        facturas = f"{d.cant_facturas_pend} por {formato_pesos_ar(d.total_facturas_pend)}"
    else:
        facturas = "ninguna"
    return (
        f"Período: {d.periodo}\n"
        f"Ingresos del mes: {formato_pesos_ar(d.total_ingresos)} ({_plural(d.cant_ingresos, 'cobro', 'cobros')})\n"
        f"Gastos del mes por categoría, de mayor a menor: {gastos}\n"
        f"Total de gastos del mes: {formato_pesos_ar(d.total_gastos)}\n"
        f"Balance del mes: {_texto_balance(d.balance)}\n"
        f"Facturas pendientes de cobro a hoy: {facturas}"
    )


def _montos_enviados(d: DatosMes) -> list[Decimal]:
    montos = [d.total_ingresos, d.total_gastos, abs(d.balance), d.total_facturas_pend]
    montos += [total for _, total in d.gastos_por_categoria]
    return [m for m in montos if m > 0]


# --- Controles sobre la respuesta de la IA ---------------------------------

_RE_MONTO = re.compile(r"\$\s?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?")
_RE_ABREVIADO = re.compile(r"(?:\$\s?)?(\d+(?:,\d+)?)\s*(millones|millón|mil)\b")
_RE_PORCENTAJE = re.compile(r"\d+(?:[.,]\d+)?\s?%")


def _cifras_no_enviadas(texto: str, permitidos: list[Decimal]) -> list[str]:
    """Montos del texto que no están entre los enviados (una cuenta propia de
    la IA o un número inventado). Se aceptan redondeos como "2,9 millones"."""
    def coincide(valor: Decimal, tolerancia: Decimal) -> bool:
        return any(abs(valor - p) <= p * tolerancia for p in permitidos)

    problemas = []
    # Primero las cifras abreviadas ("$ 2,9 millones", "431 mil"), que se
    # sacan del texto para que el "$ 2" no se lea después como otro monto.
    for m in _RE_ABREVIADO.finditer(texto):
        base = Decimal(m.group(1).replace(",", "."))
        valor = base * (Decimal(1000) if m.group(2) == "mil" else Decimal(1_000_000))
        if not coincide(valor, Decimal("0.05")):
            problemas.append(m.group(0))
    resto = _RE_ABREVIADO.sub(" ", texto)
    for m in _RE_MONTO.finditer(resto):
        entero, dec = m.group(1), m.group(2) or "0"
        valor = Decimal(entero.replace(".", "") + "." + dec)
        if not coincide(valor, Decimal("0.005")):
            problemas.append(m.group(0))
    problemas += [m.group(0) for m in _RE_PORCENTAJE.finditer(texto)]   # no se envían porcentajes
    return problemas


def _limpiar_formato(texto: str) -> str:
    """Un solo párrafo de texto plano: sin títulos, viñetas ni markdown."""
    lineas = []
    for linea in texto.splitlines():
        l = linea.strip()
        if not l or l.startswith("#"):
            continue
        es_vineta = re.match(r"^(?:[-*•]|\d+[.)])\s+", l) is not None
        l = re.sub(r"^(?:[-*•]|\d+[.)])\s+", "", l)
        sin_marcas = l.replace("**", "").replace("__", "").strip()
        # título suelto en negrita ("**Resumen financiero – Septiembre**")
        if l.startswith("**") and l.endswith("**") and not sin_marcas.endswith((".", "!", "?")):
            continue
        # una viñeta sin puntuación se cierra con punto para que no quede
        # pegada a la siguiente al unir todo en un párrafo
        if es_vineta and not sin_marcas.endswith((".", "!", "?", ":", ";", ",")):
            sin_marcas += "."
        lineas.append(sin_marcas)
    texto = " ".join(lineas).replace("*", "").replace("`", "")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.strip('"“”«» ')


_RE_FIN_ORACION = re.compile(r"(?<=[.!?…])\s+")


def _oraciones_completas(texto: str, max_palabras: int = MAX_PALABRAS_RESUMEN) -> str:
    """Descarta una oración final incompleta (respuesta cortada) y recorta en
    la última oración completa que entra en el máximo de palabras."""
    oraciones = [o for o in _RE_FIN_ORACION.split(texto) if o]
    if oraciones and not oraciones[-1].rstrip('"”)»').endswith((".", "!", "?", "…")):
        oraciones.pop()
    resultado, palabras = [], 0
    for oracion in oraciones:
        n = len(oracion.split())
        if palabras + n > max_palabras:
            break
        resultado.append(oracion)
        palabras += n
    return " ".join(resultado)


def _pulir_respuesta(contenido: str, cortada: bool = False) -> str:
    texto = _limpiar_formato(contenido or "")
    if cortada:
        # Groq avisó que se quedó sin tokens (finish_reason="length"): la
        # última oración quedó a medias aunque termine en un punto (por
        # ejemplo, en el punto de miles de un monto). Se descarta siempre.
        oraciones = [o for o in _RE_FIN_ORACION.split(texto) if o]
        texto = " ".join(oraciones[:-1])
    return _oraciones_completas(texto)


def _problema_del_texto(texto: str, permitidos: list[Decimal]) -> str | None:
    palabras = len(texto.split())
    if palabras < MIN_PALABRAS_RESUMEN:
        return f"demasiado corto ({palabras} palabras)"
    raras = _cifras_no_enviadas(texto, permitidos)
    if raras:
        return f"cifras que no estaban en los datos: {raras}"
    return None


def _redactar_con_ia(d: DatosMes) -> tuple[str | None, str | None]:
    """Devuelve (texto, None) si la IA produjo un resumen válido, o
    (None, motivo) si hay que usar la plantilla local."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, "sin_clave"

    modelo = os.getenv("GROQ_MODEL", GROQ_MODELO_POR_DEFECTO)
    mensajes = [
        {"role": "system", "content": INSTRUCCIONES_RESUMEN},
        {"role": "user", "content": _datos_para_ia(d) + "\n\nEscribí el resumen."},
    ]
    # Los modelos gpt-oss aceptan cuánto "razonar": poco alcanza para redactar
    # y deja el presupuesto de tokens para el texto. Otros modelos rechazarían
    # el parámetro, por eso solo se envía a esta familia.
    extra = {"reasoning_effort": "low"} if "gpt-oss" in modelo else None
    permitidos = _montos_enviados(d)

    try:
        cliente = Groq(api_key=api_key, timeout=GROQ_TIMEOUT, max_retries=GROQ_REINTENTOS_RED)
    except Exception as e:
        logger.error("Groq: no se pudo crear el cliente: %s", e)
        return None, "servicio_no_disponible"

    for intento in range(1, INTENTOS_IA + 1):
        try:
            respuesta = cliente.chat.completions.create(
                model=modelo,
                messages=mensajes,
                max_tokens=GROQ_MAX_TOKENS,
                temperature=GROQ_TEMPERATURA,
                extra_body=extra,
            )
        except RateLimitError as e:
            # Cuota del plan superada (el gratuito admite 8.000 tokens por
            # minuto, unos 11 resúmenes): se informa aparte porque se resuelve
            # esperando unos segundos.
            logger.warning("Groq: límite de uso alcanzado: %s", e)
            return None, "limite_de_uso"
        except Exception as e:
            # Error de red, timeout, clave inválida o modelo dado de baja: no
            # tiene sentido reintentar, se responde ya con la plantilla.
            logger.error("Groq: error al generar el resumen: %s", e)
            return None, "servicio_no_disponible"

        eleccion = respuesta.choices[0]
        texto = _pulir_respuesta(eleccion.message.content, cortada=eleccion.finish_reason == "length")
        problema = _problema_del_texto(texto, permitidos)
        if problema is None:
            return texto, None
        logger.warning(
            "Groq: resumen descartado (intento %d, finish_reason=%s): %s",
            intento, eleccion.finish_reason, problema,
        )

    return None, "respuesta_descartada"


def _plantilla_local(d: DatosMes) -> str:
    """Reserva local (HU-11): mismo contenido, con redacción fija. Se usa si
    Groq no responde o si su texto no pasó los controles."""
    if d.cant_ingresos:
        ingresos = f"cobraste {formato_pesos_ar(d.total_ingresos)} en {_plural(d.cant_ingresos, 'ingreso', 'ingresos')}"
    else:
        ingresos = "no registraste ingresos"
    if d.gastos_por_categoria:
        gastos = f"tus gastos sumaron {formato_pesos_ar(d.total_gastos)}"
    else:
        gastos = "no registraste gastos"

    partes = [f"En {d.periodo} {ingresos} y {gastos}: el mes cerró con {_texto_balance(d.balance)}."]
    if d.gastos_por_categoria:
        categoria, total = d.gastos_por_categoria[0]
        partes.append(f"El rubro con más gasto fue {categoria}, con {formato_pesos_ar(total)}.")
    if d.cant_facturas_pend:
        pendientes = _plural(d.cant_facturas_pend, "factura pendiente", "facturas pendientes")
        partes.append(f"Hoy tenés {pendientes} de cobro por {formato_pesos_ar(d.total_facturas_pend)}.")
    else:
        partes.append("Hoy no tenés facturas pendientes de cobro.")
    return " ".join(partes)


def generar_resumen_financiero(usuario_id: int, db: Session, mes: int, anio: int) -> ResultadoResumen:
    datos = _datos_del_mes(db, usuario_id, mes, anio)

    # Mes sin actividad: no tiene sentido invocar la IA (devolvía textos raros
    # mezclando facturas pendientes de otros meses). Mostramos un mensaje claro.
    if datos.cant_ingresos == 0 and not datos.gastos_por_categoria:
        mensaje = (
            f"No registramos ingresos ni gastos en {datos.periodo}. "
            f"Cuando cargues movimientos de este mes, vas a ver acá el resumen de tu situación financiera."
        )
        return ResultadoResumen(mensaje, False, True)

    texto, motivo = _redactar_con_ia(datos)
    if texto:
        return ResultadoResumen(texto, True, False)
    return ResultadoResumen(_plantilla_local(datos), False, False, motivo)


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
                # Puede ser "ml_propio" (modelo reentrenado del usuario) o
                # "ml_base" (modelo compartido). Nunca un servicio externo.
                "fuente": resultado_ml["fuente"],
                "confianza": resultado_ml["confianza"],
                "requiere_revision": False,
            }
        # Confianza insuficiente: no asumimos categoría, devolvemos "Otros"
        # como placeholder y delegamos al usuario la corrección.
        return {
            "categoria_sugerida": "Otros",
            "fuente": resultado_ml["fuente"],
            "confianza": resultado_ml["confianza"],
            "requiere_revision": True,
        }
    except Exception as e:
        logger.error(f"Error ML clasificar_gasto usuario {usuario_id}: {e}")
        return {
            "categoria_sugerida": "Otros",
            "fuente": "ml_base",
            "confianza": 0.0,
            "requiere_revision": True,
        }
