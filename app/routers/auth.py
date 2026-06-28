"""
Router de Autenticación — registro y login de usuarios.

Expone bajo /auth el registro de cuentas y el login. Al iniciar sesión genera
un token JWT que el frontend guarda y envía en cada request para identificarse.
Las contraseñas se guardan siempre hasheadas (bcrypt), nunca en texto plano.

Endpoints:
  POST /auth/register → crea una cuenta nueva.
  POST /auth/login    → valida credenciales y devuelve el token JWT.
"""

from fastapi import APIRouter, Depends, HTTPException, status
# APIRouter → agrupa endpoints relacionados, se registra en main.py con include_router
# Depends → inyección de dependencias de FastAPI (para obtener la sesión de BD)
# HTTPException → para devolver errores HTTP con código y mensaje
# status → constantes de códigos HTTP, ej: status.HTTP_400_BAD_REQUEST

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
# Session → tipo de la conexión a la BD

from app.database import get_db
# get_db → función que abre y cierra la sesión de BD automáticamente

from app.schemas.usuario import UsuarioCreate, Token, UsuarioResponse
# los schemas de Pydantic que validan los datos de entrada y salida

from app.services.auth import (
    obtener_usuario_por_email,
    crear_usuario,
    verificar_password,
    crear_token,
)
# las funciones de lógica de negocio que implementamos en services/auth.py


# -------------------------------------------------------------------
# CONFIGURACIÓN DEL ROUTER
# -------------------------------------------------------------------
router = APIRouter(
    prefix="/auth",
    # todos los endpoints de este router van a empezar con /auth
    # ej: /auth/register, /auth/login

    tags=["Autenticación"],
    # agrupa los endpoints bajo el título "Autenticación" en /docs (Swagger)
)


# -------------------------------------------------------------------
# POST /auth/register
# Crea un nuevo usuario en el sistema
# -------------------------------------------------------------------
@router.post(
    "/register",
    response_model=UsuarioResponse,
    # le dice a FastAPI qué schema usar para serializar la respuesta
    # filtra automáticamente campos sensibles como password_hash

    status_code=status.HTTP_201_CREATED,
    # 201 Created → estándar HTTP para recursos creados exitosamente
)
def register(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    # usuario_data → Pydantic valida automáticamente el body del request
    # db → FastAPI inyecta la sesión de BD usando get_db

    usuario_existente = obtener_usuario_por_email(db, usuario_data.email)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario registrado con ese email",
            # detail → mensaje que recibe el cliente en el JSON de error
        )

    nuevo_usuario = crear_usuario(
        db=db,
        nombre=usuario_data.nombre,
        email=usuario_data.email,
        password=usuario_data.password,
        # el servicio se encarga de hashear el password antes de guardarlo
    )

    return nuevo_usuario
    # FastAPI usa UsuarioResponse para serializar → excluye password_hash


# -------------------------------------------------------------------
# POST /auth/login
# Autentica un usuario y devuelve un JWT
# -------------------------------------------------------------------
@router.post(
    "/login",
    response_model=Token,
    # la respuesta va a ser el schema Token: {access_token, token_type}
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm usa "username" como campo estándar → lo mapeamos al email
    # esto activa el botón Authorize de Swagger automáticamente

    usuario = obtener_usuario_por_email(db, form_data.username)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password incorrectos",
            # intencionalmente no decimos si el email no existe o el password es incorrecto
            # dar esa info ayudaría a un atacante a enumerar usuarios válidos
        )

    password_valido = verificar_password(form_data.password, usuario.password_hash)
    if not password_valido:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password incorrectos",
        )

    if not usuario.es_activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
            # 403 Forbidden → el usuario existe y se autenticó, pero no tiene acceso
        )

    token = crear_token(data={"sub": str(usuario.id)})
    # "sub" (subject) es el campo estándar de JWT para identificar al usuario
    # guardamos el id como string porque JWT trabaja con strings

    return {"access_token": token, "token_type": "bearer"}
    # Pydantic valida que esto matchee con el schema Token antes de enviarlo
