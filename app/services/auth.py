from passlib.context import CryptContext
# CryptContext → maneja el hasheo de passwords, soporta múltiple algoritmos
# nosotros vamos a usar bcrypt, que es el estándar actual

from jose import JWTError, jwt
# jwt → genera y decodifica tokens JWT
# JWTError → excepción que lanza jose si el token es inválido o expiró

from datetime import datetime, timedelta, timezone
# timedelta → para calcular cuándo vence el token, ej: "en 7 días"
# timezone → para trabajar con fechas UTC (evita bugs de zona horaria)

from sqlalchemy.orm import Session
# Session → tipo de la conexión a la BD que recibimos por inyección de dependencia

from app.models.usuario import Usuario
# el modelo SQLAlchemy de la tabla usuarios

import os
# para leer las variables de entorno (SECRET_KEY, etc.)


# -------------------------------------------------------------------
# CONFIGURACIÓN DE BCRYPT
# -------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# schemes=["bcrypt"] → usamos bcrypt como algoritmo de hasheo
# deprecated="auto" → si en el futuro cambiamos el algoritmo,
#                     los hashes viejos se migran automáticamente


# -------------------------------------------------------------------
# CONFIGURACIÓN DE JWT
# -------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
# clave secreta para firmar el token → está en el .env
# si alguien la conoce puede generar tokens falsos, nunca hardcodearla

ALGORITHM = "HS256"
# algoritmo de firma del JWT
# HS256 = HMAC con SHA-256, el más común para APIs internas

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))
# tiempo de vida del token en minutos
# default: 7 días (60 min × 24 hs × 7 días)
# el usuario no tiene que loguearse de nuevo durante ese tiempo


# -------------------------------------------------------------------
# FUNCIONES DE PASSWORD
# -------------------------------------------------------------------
def hashear_password(password: str) -> str:
    # convierte el password en texto plano a un hash bcrypt
    # ej: "miPassword123" → "$2b$12$eImiTXuWVxfM37uY4JANjQ..."
    # el hash es distinto cada vez aunque el password sea el mismo (bcrypt usa salt)
    return pwd_context.hash(password)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    # compara el password que manda el usuario con el hash guardado en la BD
    # devuelve True si coinciden, False si no
    # Analogía: es como comparar una llave con una cerradura
    return pwd_context.verify(password_plano, password_hash)


# -------------------------------------------------------------------
# FUNCIONES DE JWT
# -------------------------------------------------------------------
def crear_token(data: dict) -> str:
    # genera un JWT firmado con los datos del usuario
    # data → diccionario con lo que queremos guardar en el token
    #        generalmente {"sub": str(usuario_id)}

    payload = data.copy()
    # copiamos para no modificar el dict original

    expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # calculamos cuándo vence el token desde ahora

    payload.update({"exp": expiracion})
    # "exp" es un campo estándar de JWT → jose lo usa automáticamente
    # para rechazar tokens vencidos

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    # jwt.encode firma el payload con nuestra SECRET_KEY y devuelve el token string


def decodificar_token(token: str) -> dict | None:
    # decodifica y valida un JWT
    # devuelve el payload si el token es válido, None si no lo es
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # jwt.decode verifica la firma y que no esté vencido
        # si algo falla lanza JWTError
        return payload
    except JWTError:
        # token inválido, manipulado o expirado
        return None


# -------------------------------------------------------------------
# FUNCIONES DE BASE DE DATOS
# -------------------------------------------------------------------
def obtener_usuario_por_email(db: Session, email: str) -> Usuario | None:
    # busca un usuario en la BD por su email
    # devuelve el objeto Usuario si existe, None si no
    return db.query(Usuario).filter(Usuario.email == email).first()


def crear_usuario(db: Session, nombre: str, email: str, password: str) -> Usuario:
    # crea un nuevo usuario en la BD
    # hashea el password antes de guardarlo

    password_hash = hashear_password(password)
    # nunca guardamos el password en texto plano

    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email,
        password_hash=password_hash,
    )

    db.add(nuevo_usuario)       # agrega el objeto a la sesión
    db.commit()                 # ejecuta el INSERT en PostgreSQL
    db.refresh(nuevo_usuario)   # recarga el objeto para obtener el id generado por la BD
    return nuevo_usuario
