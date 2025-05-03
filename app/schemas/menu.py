# app/schemas/menu.py

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime # <<< IMPORTACIÓN AÑADIDA

# --- Base Schema ---
class MenuBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    icono: Optional[str] = Field(None, max_length=50)
    ruta: Optional[str] = Field(None, max_length=255)
    padre_menu_id: Optional[int] = None
    orden: Optional[int] = None
    area_id: Optional[int] = None # Ahora incluimos area_id
    es_activo: bool = True # Por defecto activo al crear/actualizar si no se especifica

    class Config:
        from_attributes = True # Permite crear desde objetos ORM/diccionarios

# --- Schema para Crear ---
class MenuCreate(MenuBase):
    # Hereda todos los campos de MenuBase.
    # Podrías hacer algunos campos obligatorios aquí si es necesario
    # Por ejemplo, asegurar que 'nombre' siempre se proporcione.
    # 'es_activo' por defecto es True en MenuBase.
    pass

# --- Schema para Actualizar ---
# Todos los campos son opcionales en la actualización
class MenuUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    icono: Optional[str] = Field(None, max_length=50)
    ruta: Optional[str] = Field(None, max_length=255)
    padre_menu_id: Optional[int] = None
    orden: Optional[int] = None
    area_id: Optional[int] = None
    es_activo: Optional[bool] = None # Permitir activar/desactivar

    # Validación para asegurar que al menos un campo se envía para actualizar
    @field_validator('*', mode='before')
    @classmethod
    def check_at_least_one_value(cls, v, info):
         # Esta validación es compleja de implementar correctamente aquí.
         # Es mejor validar en el endpoint/servicio que el payload no esté vacío.
         return v

# --- Schema para Leer (Jerarquía - MenuItem existente) ---
# Asegúrate que este schema coincida con las columnas devueltas por sp_GetAllMenuItemsAdmin
# y las usadas por build_menu_tree
class MenuItem(BaseModel):
    menu_id: int
    nombre: str
    icono: Optional[str] = None
    ruta: Optional[str] = None
    orden: Optional[int] = None
    es_activo: bool
    area_id: Optional[int] = None # Añadir area_id
    # Asumiendo que el SP puede devolver el nombre del área con un JOIN
    area_nombre: Optional[str] = None
    # Asumiendo que el SP devuelve el nivel (si lo usas en build_menu_tree)
    level: Optional[int] = None # Hacer opcional si no siempre viene

    children: List[MenuItem] = [] # Llenado por build_menu_tree

    class Config:
        from_attributes = True

# --- Schema para la Respuesta Jerárquica (Existente) ---
class MenuResponse(BaseModel):
    menu: List[MenuItem]

    class Config:
        from_attributes = True

# --- Schema para Leer un ÚNICO item (sin hijos) ---
class MenuReadSingle(MenuBase): # Hereda campos base
    menu_id: int
    # Podrías añadir aquí el nombre del área si haces JOIN en la consulta individual
    area_nombre: Optional[str] = None

    # --- CORRECCIÓN APLICADA AQUÍ ---
    fecha_creacion: datetime # Cambiado de Optional[str] a datetime
    # Añadido fecha_actualizacion también como datetime opcional
    fecha_actualizacion: Optional[datetime] = None
    # --- FIN DE LA CORRECCIÓN ---

    class Config:
        from_attributes = True

# --- (Opcional) Actualizar referencias si usas Pydantic v1 o tienes problemas ---
# MenuItem.update_forward_refs()