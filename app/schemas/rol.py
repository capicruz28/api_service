# app/schemas/rol.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class RolBase(BaseModel):
    """Schema base para roles, sin ID."""
    nombre: str = Field(..., min_length=3, max_length=50, description="Nombre único del rol")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción detallada del rol")
    es_activo: bool = Field(True, description="Indica si el rol está activo")

class RolCreate(RolBase):
    """Schema para la creación de un nuevo rol."""
    pass # Hereda todos los campos de RolBase

class RolUpdate(BaseModel):
    """Schema para actualizar un rol. Todos los campos son opcionales."""
    nombre: Optional[str] = Field(None, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    es_activo: Optional[bool] = None

class RolRead(RolBase):
    """Schema para leer datos de un rol, incluye el ID y fecha de creación."""
    rol_id: int = Field(..., description="ID único del rol")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del rol")

    class Config:
        from_attributes = True # Para compatibilidad si se usa con ORM o objetos similares