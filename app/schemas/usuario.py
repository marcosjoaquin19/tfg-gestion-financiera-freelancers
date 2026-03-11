from pydantic import BaseModel, EmailStr, ConfigDict, Field
# BaseModel → clase base de Pydantic, valida los datos automáticamente
# EmailStr → tipo especial que verifica que el string sea un email válido
# ConfigDict → reemplaza class Config en Pydantic V2
# Field → permite agregar validaciones extra a los campos

# -------------------------------------------------------------------
# SCHEMA DE REGISTRO
# Se usa cuando alguien hace POST /auth/register
# Pydantic va a validar que el body del request tenga estos campos
# -------------------------------------------------------------------
class UsuarioCreate(BaseModel):
    nombre: str
    # nombre completo del usuario, ej: "Marcos Joaquín"

    email: EmailStr
    # Pydantic verifica automáticamente que sea un email válido
    # si mandan "marcos@@", devuelve error 422 sin que vos hagas nada

    password: str = Field(min_length=8, max_length=128)
    # el password en texto plano que manda el usuario
    # NUNCA se guarda así en la BD → el servicio lo hashea antes de guardarlo


# -------------------------------------------------------------------
# SCHEMA DE LOGIN
# Se usa cuando alguien hace POST /auth/login
# Solo necesita email y password para autenticarse
# -------------------------------------------------------------------
class UsuarioLogin(BaseModel):
    email: EmailStr
    # el email con el que se registró

    password: str
    # el password en texto plano para comparar contra el hash guardado


# -------------------------------------------------------------------
# SCHEMA DE RESPUESTA DE TOKEN
# Lo que la API devuelve después de un login exitoso
# El frontend guarda este token y lo manda en cada request posterior
# -------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    # el JWT generado, ej: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    # el frontend lo guarda y lo manda en el header Authorization: Bearer <token>

    token_type: str
    # siempre va a ser "bearer" → es el estándar para JWT en HTTP


# -------------------------------------------------------------------
# SCHEMA DE RESPUESTA DE USUARIO
# Lo que la API devuelve cuando crea o consulta un usuario
# NO incluye password_hash → nunca exponemos datos sensibles
# -------------------------------------------------------------------
class UsuarioResponse(BaseModel):
    id: int
    # el ID generado por PostgreSQL al crear el usuario

    nombre: str
    # nombre del usuario

    email: EmailStr
    # email del usuario

    es_activo: bool
    # si el usuario está activo o fue desactivado

    model_config = ConfigDict(from_attributes=True)
    # le dice a Pydantic que puede leer los datos desde un objeto SQLAlchemy
    # sin esto, solo podría leer desde diccionarios
    # Analogía: es el "traductor" entre el objeto de la BD y el JSON de respuesta
