"""
Punto de entrada de la API (backend) — FreelanceControl.
==========================================================

Este archivo es el "arranque" de toda la aplicación del lado del servidor.
Cuando se levanta el backend (uvicorn app.main:app), se ejecuta este módulo y
queda corriendo la API REST que el frontend (React) consume.

¿Qué hace, paso a paso?
  1. Carga las variables de entorno del archivo .env (claves, conexión a la BD).
  2. Verifica que haya una clave de firma segura (si no, no arranca).
  3. Crea las tablas que falten (red de seguridad: las migraciones ya corrieron).
  4. Construye la aplicación FastAPI con su título y versión.
  5. Habilita CORS para que el frontend (localhost:3000) pueda llamar a la API.
  6. Registra (incluye) todos los "routers", es decir, cada módulo funcional
     de la app: autenticación, ingresos, gastos, facturas, etc.

Mapa de módulos de la aplicación (cada router = una sección de la app):
  - auth            → registro / login con JWT (seguridad y sesiones).
  - ingresos        → registro y consulta de ingresos del freelancer.
  - gastos          → registro de gastos (con categorización por ML).
  - facturas        → registro y seguimiento de las facturas emitidas (pendiente/pagada/vencida).
  - alertas         → auditoría: detecta registros sospechosos o inconsistentes.
  - proyecciones    → predicción de ingresos futuros (modelo Prophet).
  - resumen         → resumen financiero mensual redactado con IA (Groq).
  - recomendaciones → sugerencias armadas con reglas fijas sobre los datos (sin IA).
  - importar        → carga masiva de movimientos desde extractos bancarios (CSV o Excel).
  - monotributo     → control fiscal del monotributo argentino (categoría/límites).
  - ml              → clasificador de gastos por texto (Machine Learning local).
  - reportes        → reporte PDF con el resumen del mes cerrado.

Vocabulario que aparece en todo el backend:
  - API REST: la "ventanilla" por la que la pantalla (React) le pide cosas al
    servidor. Cada pedido es un verbo + una dirección: GET /gastos (traer),
    POST /gastos (crear), PUT (reemplazar), PATCH (cambiar una parte), DELETE (borrar).
  - Endpoint: cada una de esas combinaciones verbo + dirección (por ejemplo,
    POST /auth/login). Es lo que en los comentarios también se llama "ruta".
  - Request / response: el pedido que llega y la respuesta que se devuelve.
    El pedido tiene encabezados (headers, como el token) y un cuerpo (body,
    los datos del formulario en formato JSON).
  - Router: el archivo que agrupa los endpoints de una sección (app/routers/).
  - Service: donde vive la lógica de negocio (app/services/); los routers lo llaman.
  - Model: la clase que representa una tabla de la base (app/models/).
  - Schema: el "molde" que valida los datos que entran y salen (app/schemas/,
    con la biblioteca Pydantic). Si un dato no cumple el molde, la API
    responde 422 sin llegar a ejecutar la lógica.
  - Códigos de respuesta: 200 OK, 201 creado, 204 borrado (sin contenido),
    400/422 datos inválidos, 401 sin sesión, 403 sin permiso, 404 no
    encontrado, 409 conflicto con el estado actual, 500 error del servidor.
"""

# PATRÓN: Arquitectura en capas (Layered Architecture) — routers → services → models.
# PATRÓN: Registro centralizado de routers (Front Controller): app.include_router().
# Justificación y alternativas descartadas: defensa_final/02_ARQUITECTURA_Y_PATRONES.md

import math

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.database import engine
from app import models
from app.routers import auth, ingresos, gastos, facturas, alertas, proyecciones, resumen, recomendaciones, importar, monotributo, ml, reportes

# Carga las variables del archivo .env (ej: DATABASE_URL, SECRET_KEY, GROQ_API_KEY)
load_dotenv()

# Sin una clave de firma segura la API no arranca: mejor un error claro al
# levantar que tokens falsificables en producción (HU-17).
from app.services.auth import SECRET_KEY, validar_clave_de_firma  # noqa: E402
validar_clave_de_firma(SECRET_KEY)

# Crea las tablas que falten a partir de los modelos de SQLAlchemy. Con Docker
# este paso no hace nada: antes de levantar la API, el contenedor corre
# "alembic upgrade head" (ver Dockerfile) y las tablas ya existen. Queda como
# red de seguridad si se levanta uvicorn a mano sobre una base vacía.
models.Base.metadata.create_all(bind=engine)

# Instancia principal de la API. El title/description/version aparecen en la
# documentación automática que FastAPI publica en /docs (Swagger UI).
app = FastAPI(
    title="Sistema de Gestión Financiera para Freelancers",
    description="API REST para gestión financiera con auditoría y predicciones",
    version="1.0.0"
)

def _valores_serializables(valor):
    """Reemplaza NaN e Infinity por texto dentro del detalle de un error."""
    if isinstance(valor, float) and not math.isfinite(valor):
        return str(valor)
    if isinstance(valor, dict):
        return {k: _valores_serializables(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_valores_serializables(v) for v in valor]
    return valor


def _sin_prefijo_value_error(errores: list) -> list:
    """Quita el "Value error, " que la librería antepone a los mensajes propios.

    Los validadores del sistema lanzan sus mensajes en castellano ("El monto
    debe ser mayor a cero"), pero la librería de validación les agrega ese
    prefijo en inglés, y la pantalla lo mostraba tal cual al usuario.
    """
    for error in errores:
        if error.get("type") == "value_error" and isinstance(error.get("msg"), str):
            error["msg"] = error["msg"].removeprefix("Value error, ")
    return errores


@app.exception_handler(RequestValidationError)
async def error_de_validacion(request: Request, exc: RequestValidationError):
    """Misma respuesta 422 que arma FastAPI por defecto, con una salvedad.

    El detalle del error repite el valor recibido. Si alguien manda un monto
    NaN o Infinity (el lector de JSON de Python los acepta), ese valor no se
    puede volver a escribir en JSON y el propio mensaje de error terminaba en
    un 500. Acá se lo convierte a texto antes de responder.
    """
    return JSONResponse(
        status_code=422,
        content={"detail": _sin_prefijo_value_error(
            _valores_serializables(jsonable_encoder(exc.errors()))
        )},
    )


# CORS: por seguridad, el navegador bloquea que una web llame a otra de distinto
# origen. Acá autorizamos explícitamente al frontend (React, puerto 3000/3001)
# a consumir la API. Solo se permiten esos orígenes y los métodos HTTP listados.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Registro de routers: cada uno aporta un grupo de endpoints (rutas) y queda
# montado bajo su propio prefijo (ej: /ingresos, /gastos). Este es el "índice"
# de todas las funcionalidades expuestas por la API.
app.include_router(auth.router)
app.include_router(ingresos.router)
app.include_router(gastos.router)
app.include_router(facturas.router)
app.include_router(alertas.router)
app.include_router(proyecciones.router)
app.include_router(resumen.router)
app.include_router(recomendaciones.router)
app.include_router(importar.router)
app.include_router(monotributo.router)
app.include_router(ml.router)
app.include_router(reportes.router)

# Endpoint raíz: respuesta simple para confirmar a simple vista que la API
# está levantada (útil al abrir http://localhost:8000 en el navegador).
@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente ✅"}

# Endpoint de "health check": los scripts de arranque (start.command y
# start.bat) lo consultan en bucle y abren el navegador recién cuando responde.
@app.get("/health")
def health_check():
    return {"status": "ok", "servicio": "TFG Freelancers API"}