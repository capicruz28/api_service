# app/schemas/rol_menu_permiso.py
from pydantic import BaseModel, Field
from typing import Optional

class RolMenuPermisoBase(BaseModel):
    """Schema base para los permisos de rol sobre un menú."""
    rol_id: int = Field(..., description="ID del rol asociado")
    menu_id: int = Field(..., description="ID del menú asociado")
    puede_ver: bool = Field(True, description="Permiso para ver el menú")
    puede_editar: bool = Field(False, description="Permiso para editar (si aplica)")
    puede_eliminar: bool = Field(False, description="Permiso para eliminar (si aplica)")

class RolMenuPermisoCreate(RolMenuPermisoBase):
    """Schema para crear un nuevo permiso."""
    pass

class RolMenuPermisoUpdate(BaseModel):
    """Schema para actualizar permisos existentes. Todos opcionales."""
    puede_ver: Optional[bool] = None
    puede_editar: Optional[bool] = None
    puede_eliminar: Optional[bool] = None

class RolMenuPermisoRead(RolMenuPermisoBase):
    """Schema para leer los datos de un permiso."""
    rol_menu_id: int = Field(..., description="ID único del permiso")
    # Podríamos añadir aquí detalles del rol y menú si hacemos JOINs en el servicio
    # rol: Optional[RolRead] = None # Ejemplo
    # menu: Optional[MenuRead] = None # Ejemplo

    class Config:
        from_attributes = True