# app/schemas/auth.py (ACTUALIZADO Y RECOMENDADO)

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# --- Schema Base para Datos del Usuario ---
# Define los campos básicos que esperas para un usuario.
# Puedes mover esto a app/schemas/usuario.py si lo prefieres y luego importarlo.
class UserDataBase(BaseModel):
    usuario_id: int
    nombre_usuario: str
    correo: EmailStr # Usa EmailStr para validación de email
    nombre: Optional[str] = None # Campos opcionales si pueden ser NULL en la BD
    apellido: Optional[str] = None
    es_activo: bool

    # Configuración para permitir el uso desde ORM (si usas SQLAlchemy más adelante)
    # class Config:
    #     orm_mode = True # o from_attributes = True en Pydantic v2

# --- Schema para UserData incluyendo Roles ---
# Hereda de UserDataBase y añade el campo 'roles'.
class UserDataWithRoles(UserDataBase):
    roles: List[str] = Field(default_factory=list) # Lista de strings para los nombres de roles

# --- Schema para los datos de entrada del Login ---
# (Ya lo tenías, sin cambios necesarios aquí)
class LoginData(BaseModel):
    username: str
    password: str

# --- Schema para la Respuesta del Token (ACTUALIZADO) ---
# Ahora usa UserDataWithRoles para el campo user_data.
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" # Puedes poner un valor por defecto
    user_data: UserDataWithRoles # <-- Cambio principal: usa el schema específico

# --- Schema para el Payload dentro del JWT ---
# (Opcional, si necesitas definir la estructura del payload del token)
class TokenPayload(BaseModel):
    sub: Optional[str] = None # 'sub' (subject) es estándar para el identificador del usuario (username)
    # Podrías añadir otros campos si los incluyes en create_access_token
    # exp: Optional[int] = None # Pydantic puede manejar la expiración si la pones aquí
    # roles: Optional[List[str]] = None