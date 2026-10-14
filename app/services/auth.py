"""
Servicio de Autenticación — seguridad de contraseñas y tokens JWT.

Centraliza las funciones de seguridad: hashear y verificar contraseñas (bcrypt)
y crear/decodificar los tokens JWT que identifican al usuario en cada pedido
(request) a la API. Lo usan la ruta de auth (login/registro) y la dependencia
get_current_user, que protege todas las demás rutas.

Las dos ideas clave, en criollo:
  - Hash de contraseña: es como una licuadora de una sola dirección. La
    contraseña entra y sale un "jugo" (el hash) del que no se puede volver a
    la contraseña. En la base se guarda solo el hash; al iniciar sesión se
    licúa lo que escribió el usuario y se compara con el guardado.
  - Token JWT: es como la pulsera de un boliche. Al hacer login el servidor
    entrega una pulsera firmada que dice quién sos y hasta cuándo vale; en cada
    pedido siguiente el navegador la muestra y el servidor verifica la firma,
    sin volver a pedir la contraseña.
"""

# PATRÓN: Facade de seguridad — hash, verificación y firma de tokens en un solo punto.
# (Facade = "fachada": el resto del sistema usa estas pocas funciones sin
# conocer los detalles de bcrypt ni de JWT.)
# Justificación y alternativas descartadas: defensa_final/02_ARQUITECTURA_Y_PATRONES.md

from passlib.context import CryptContext
# CryptContext → maneja el hash de las contraseñas; soporta varios algoritmos.
# Usamos bcrypt, el estándar actual para contraseñas.

from jose import JWTError, jwt
# jwt → genera y decodifica tokens JWT
# JWTError → excepción que lanza jose si el token es inválido o expiró

from datetime import datetime, timedelta, timezone
# timedelta → para calcular cuándo vence el token, ej: "en 7 días"
# timezone → para trabajar con fechas UTC (evita errores de zona horaria)

from sqlalchemy import func
from sqlalchemy.orm import Session
# Session → tipo de la conexión a la BD que recibimos por inyección de dependencia

from app.models.usuario import Usuario
# el modelo SQLAlchemy de la tabla usuarios

import os
# para leer las variables de entorno (SECRET_KEY, etc.)

import logging
logging.getLogger("passlib").setLevel(logging.ERROR)
# passlib 1.7 busca bcrypt.__about__, que las versiones nuevas de bcrypt ya no
# traen, y lo avisa con un traceback "(trapped) error reading bcrypt version".
# El hash funciona igual: se silencia para que el aviso no parezca un error
# al correr los seeds o al leer los logs.


# -------------------------------------------------------------------
# CONFIGURACIÓN DE BCRYPT
# -------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# schemes=["bcrypt"] → usamos bcrypt como algoritmo de hash
# deprecated="auto" → si en el futuro cambiamos de algoritmo, los hashes viejos
#                     se siguen aceptando y se marcan para actualizarse
# bcrypt es lento A PROPÓSITO (costo 12 = 2^12 vueltas, el "12" que se ve en
# "$2b$12$..."): para un usuario que inicia sesión es imperceptible, pero para
# alguien que roba la base e intenta adivinar millones de contraseñas, cada
# intento le cuesta caro.


# -------------------------------------------------------------------
# CONFIGURACIÓN DE JWT
# -------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
# Clave secreta para firmar el token → se lee del archivo .env (no está en el
# repositorio). Si alguien la conoce puede generar tokens falsos: por eso nunca
# se escribe en el código.

# Valor de ejemplo de .env.example. Es público (está en el repositorio): con
# esa clave cualquiera podría firmar tokens válidos para cualquier usuario.
CLAVE_DE_EJEMPLO = "generar_una_clave_aleatoria_y_pegarla_aca"
# Largo mínimo: 32 caracteres (secrets.token_urlsafe(48) genera 64).
LARGO_MINIMO_CLAVE = 32


def validar_clave_de_firma(clave: str | None) -> None:
    """Frena el arranque de la API si la clave de firma no es segura.

    Sin este control, una clave faltante recién fallaba en el primer login
    (error 500), y la clave de ejemplo funcionaba en silencio.

    Tres casos rechazados: que no haya clave, que sea la de ejemplo (pública) o
    que tenga menos de 32 caracteres. La llama main.py al arrancar.
    """
    if not clave:
        raise RuntimeError(
            "Falta SECRET_KEY en el entorno. Generala con: "
            'python -c "import secrets; print(secrets.token_urlsafe(48))" y cargala en el .env.'
        )
    if clave == CLAVE_DE_EJEMPLO:
        raise RuntimeError(
            "SECRET_KEY tiene el valor de ejemplo de .env.example, que es público. "
            "Generá una clave propia antes de levantar la API."
        )
    if len(clave) < LARGO_MINIMO_CLAVE:
        raise RuntimeError(
            f"SECRET_KEY es demasiado corta ({len(clave)} caracteres): "
            f"se exigen al menos {LARGO_MINIMO_CLAVE}."
        )

ALGORITHM = "HS256"
# algoritmo de firma del JWT
# HS256 = HMAC con SHA-256, el más común para APIs internas

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))
# Tiempo de vida del token, en minutos.
# Valor por defecto: 7 días (60 min × 24 h × 7 días).
# Durante ese tiempo el usuario no tiene que volver a iniciar sesión; al
# vencerse, la pantalla lo manda al login con el aviso "tu sesión venció".


# -------------------------------------------------------------------
# FUNCIONES DE CONTRASEÑA
# -------------------------------------------------------------------
def hashear_password(password: str) -> str:
    """Convierte la contraseña en texto plano en un hash bcrypt.

    Ejemplo: "miPassword123" → "$2b$12$eImiTXuWVxfM37uY4JANjQ..."
      - "$2b$" indica bcrypt; "12$" el costo (cuántas vueltas da el cálculo).
      - Lo que sigue incluye la "sal" y el hash propiamente dicho.

    La sal es un valor al azar que se mezcla con la contraseña antes de
    licuarla: por eso la misma contraseña da un hash distinto cada vez, y dos
    usuarios con la misma contraseña no tienen el mismo hash. Así no sirven las
    tablas de hashes precalculados que usan los atacantes.
    """
    return pwd_context.hash(password)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Compara la contraseña que escribió el usuario con el hash guardado en la base.

    No "deshashea" nada (no se puede): toma la sal que viene dentro del hash
    guardado, licúa la contraseña escrita con esa misma sal y compara los
    resultados. Devuelve True si coinciden, False si no.
    """
    return pwd_context.verify(password_plano, password_hash)


# Hash de relleno, con el mismo costo que los reales. Si el correo no existe,
# el login verifica igual contra este hash (routers/auth.py): así tarda lo
# mismo que con una contraseña incorrecta y el tiempo de respuesta no delata
# qué correos están registrados (antes: 2 ms contra 170 ms).
HASH_DE_RELLENO = hashear_password("sin-cuenta-asociada")


# -------------------------------------------------------------------
# FUNCIONES DE JWT
# -------------------------------------------------------------------
def crear_token(data: dict) -> str:
    """Genera el token JWT firmado que se le entrega al usuario al iniciar sesión.

    data es un diccionario con lo que queremos guardar en el token; acá es
    {"sub": str(usuario_id)} ("sub" = "subject", el campo estándar de JWT para
    decir de quién es el token).

    Ojo: el token va FIRMADO, no encriptado. Cualquiera que lo tenga puede leer
    su contenido (el id del usuario y la fecha de vencimiento: nada secreto),
    pero no puede cambiarlo: si le toca una sola letra, la firma deja de
    coincidir y decodificar_token() lo rechaza. Para firmar hace falta la
    SECRET_KEY, que solo tiene el servidor.
    """
    # payload = el contenido del token. Copiamos para no modificar el
    # diccionario original que nos pasaron.
    payload = data.copy()

    # Cuándo vence el token, contado desde ahora.
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload.update({"exp": expiracion})
    # "exp" es un campo estándar de JWT → jose lo usa automáticamente
    # para rechazar tokens vencidos

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    # jwt.encode firma el contenido con nuestra SECRET_KEY y devuelve el token
    # como texto: tres partes separadas por puntos (encabezado.contenido.firma).


def decodificar_token(token: str) -> dict | None:
    """Valida un token JWT y devuelve su contenido, o None si no es válido.

    La llama get_current_user (app/dependencies.py) en cada pedido a una ruta
    protegida. Si devuelve None, la API responde 401 ("no autorizado").
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # jwt.decode verifica dos cosas: que la firma corresponda a nuestra
        # SECRET_KEY (nadie lo modificó) y que no esté vencido ("exp").
        # Si algo falla, lanza JWTError.
        # algorithms=[ALGORITHM] → solo se acepta HS256; un token que diga venir
        # firmado con otro algoritmo (o con ninguno) se rechaza.
        return payload
    except JWTError:
        # token inválido, manipulado o vencido
        return None


# -------------------------------------------------------------------
# FUNCIONES DE BASE DE DATOS
# -------------------------------------------------------------------
def obtener_usuario_por_email(db: Session, email: str) -> Usuario | None:
    """Busca un usuario por su email; devuelve el Usuario o None si no existe.

    No distingue mayúsculas ni espacios alrededor: el login con
    "Demo@freelancecontrol.com" tiene que encontrar la cuenta.
    """
    return db.query(Usuario).filter(func.lower(Usuario.email) == (email or "").strip().lower()).first()


def crear_usuario(db: Session, nombre: str, email: str, password: str) -> Usuario:
    """Crea un usuario nuevo (registro). La contraseña se guarda solo como hash."""

    password_hash = hashear_password(password)
    # nunca guardamos la contraseña en texto plano

    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email.strip().lower(),
        password_hash=password_hash,
    )

    db.add(nuevo_usuario)       # agrega el objeto a la sesión
    db.commit()                 # ejecuta el INSERT en PostgreSQL
    db.refresh(nuevo_usuario)   # recarga el objeto para obtener el id generado por la BD
    return nuevo_usuario
