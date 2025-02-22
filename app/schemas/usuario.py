from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=50)
    correo: EmailStr
    nombre: Optional[str] = Field(None, max_length=50)
    apellido: Optional[str] = Field(None, max_length=50)

class UsuarioCreate(UsuarioBase):
    contrasena: str = Field(..., min_length=6)

class UsuarioResponse(BaseModel):
    usuario_id: int
    nombre_usuario: str
    correo: str
    nombre: Optional[str]
    apellido: Optional[str]
    es_activo: bool
    fecha_creacion: datetime

