# app/schemas/usuario_rol.py
from pydantic import BaseModel, Field
from datetime import datetime

class UsuarioRolBase(BaseModel):
    """Schema base para la relación usuario-rol."""
    usuario_id: int = Field(..., description="ID del usuario")
    rol_id: int = Field(..., description="ID del rol")
    es_activo: bool = Field(True, description="Indica si la asignación está activa")

class UsuarioRolCreate(BaseModel):
    """Schema específico para crear la asignación (solo IDs)."""
    # No se necesita aquí, la creación se hará por IDs en la ruta
    pass

class UsuarioRolUpdate(BaseModel):
    """Schema para actualizar el estado de la asignación (activar/desactivar)."""
    es_activo: bool

class UsuarioRolRead(UsuarioRolBase):
    """Schema para leer datos de la asignación usuario-rol."""
    usuario_rol_id: int = Field(..., description="ID único de la asignación")
    fecha_asignacion: datetime = Field(..., description="Fecha en que se realizó la asignación")

    class Config:
        from_attributes = True