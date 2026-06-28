"""
Dependencias compartidas de la API — autenticación de usuarios.

Define get_current_user, la dependencia que se inyecta en los endpoints que
requieren un usuario logueado. Lee el token JWT del header Authorization, lo
valida y devuelve el usuario correspondiente, o corta con 401/403 si el token
es inválido o la cuenta está desactivada. Es el "guardia" de las rutas privadas.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# OAuth2PasswordBearer → le dice a FastAPI cómo extraer el token del header
# espera un header: Authorization: Bearer <token>
# también documenta el esquema de auth automáticamente en /docs

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.services.auth import decodificar_token


# -------------------------------------------------------------------
# CONFIGURACIÓN DE OAUTH2
# -------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# tokenUrl → le dice a Swagger dónde está el endpoint de login
# cuando alguien hace click en "Authorize" en /docs, usa esta URL


# -------------------------------------------------------------------
# DEPENDENCIA PRINCIPAL
# Se inyecta en cualquier endpoint que requiera usuario autenticado
# Uso: current_user: Usuario = Depends(get_current_user)
# -------------------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    # FastAPI extrae automáticamente el token del header Authorization
    # si el header no está presente, devuelve 401 automáticamente

    db: Session = Depends(get_db),
    # sesión de BD para buscar el usuario
) -> Usuario:

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
        # WWW-Authenticate → header estándar HTTP que indica el esquema de auth esperado
        # algunos clientes lo usan para redirigir al login automáticamente
    )

    payload = decodificar_token(token)
    if payload is None:
        # el token es inválido, fue manipulado o ya expiró
        raise credenciales_invalidas

    usuario_id: str = payload.get("sub")
    if usuario_id is None:
        # el token no tiene el campo "sub" → está malformado
        raise credenciales_invalidas

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        # el token es válido pero el usuario fue eliminado de la BD
        raise credenciales_invalidas

    if not usuario.es_activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )

    return usuario
    # FastAPI inyecta este objeto en el endpoint que tenga Depends(get_current_user)
    # desde el endpoint podés acceder a usuario.id, usuario.email, etc.
