import os
import time
import logging
from groq import Groq
from sqlalchemy.orm import Session
from app.models.cache_clasificacion import CacheClasificacion

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
