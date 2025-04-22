# app/schemas/usuario.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List # Asegúrate de importar List
from datetime import datetime
# Importa el schema RolRead que acabamos de definir
from .rol import RolRead # Ajusta la ruta si es necesario

class UsuarioBase(BaseModel):
    """Schema base para usuarios."""
    nombre_usuario: str = Field(..., min_length=3, max_length=50)
    correo: EmailStr
    nombre: Optional[str] = Field(None, max_length=50)
    apellido: Optional[str] = Field(None, max_length=50)
    es_activo: bool = True

class UsuarioCreate(UsuarioBase):
    """Schema para crear un usuario, requiere contraseña."""
    contrasena: str = Field(..., min_length=8)

class UsuarioUpdate(BaseModel):
    """Schema para actualizar usuario. Todos los campos opcionales."""
    nombre_usuario: Optional[str] = Field(None, min_length=3, max_length=50)
    correo: Optional[EmailStr] = None
    nombre: Optional[str] = Field(None, max_length=50)
    apellido: Optional[str] = Field(None, max_length=50)
    es_activo: Optional[bool] = None
    # No incluimos contraseña aquí, debería tener su propio endpoint/proceso

class UsuarioRead(UsuarioBase):
    """Schema para leer datos básicos de un usuario."""
    usuario_id: int
    fecha_creacion: datetime
    fecha_ultimo_acceso: Optional[datetime] = None
    correo_confirmado: bool

    class Config:
        from_attributes = True

# --- NUEVO SCHEMA ---
class UsuarioReadWithRoles(UsuarioRead):
    """Schema para leer datos de un usuario incluyendo sus roles activos."""
    roles: List[RolRead] = [] # Lista para almacenar los roles

    class Config:
        from_attributes = True

# --- NUEVO SCHEMA PARA LA RESPUESTA PAGINADA ---
class PaginatedUsuarioResponse(BaseModel):
    """Schema para la respuesta paginada de la lista de usuarios."""
    usuarios: List[UsuarioReadWithRoles]
    total_usuarios: int
    pagina_actual: int
    total_paginas: int
# Podrías tener otros schemas como UsuarioInDB, etc., si los necesitas