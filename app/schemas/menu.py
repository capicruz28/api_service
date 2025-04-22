# app/schemas/menu.py (CORREGIDO)

# --- ESTA LÍNEA DEBE SER LA PRIMERA ---
from __future__ import annotations

# --- Ahora vienen las otras importaciones ---
from pydantic import BaseModel, Field
from typing import List, Optional

# --- El resto del código sigue igual ---

class MenuItem(BaseModel):
    # Usar los nombres y tipos EXACTOS devueltos por sp_GetFullMenu
    menu_id: int
    nombre: str
    icono: Optional[str] = None
    ruta: Optional[str] = None
    orden: Optional[int] = None
    # 1. Cambiar 'level' a 'Level' para que coincida con la columna del SP
    level: int # Coincide con la columna 'Level' del SP
    es_activo: bool
    # 2. Añadir 'padre_menu_id' porque viene del SP y build_menu_tree lo necesita
    padre_menu_id: Optional[int] = None # Coincide con la columna del SP

    # El campo 'children' se llena DESPUÉS por build_menu_tree, no viene de la DB
    children: List[MenuItem] = []

    # Configuración para permitir la creación desde atributos de objeto/diccionario
    class Config:
        from_attributes = True
        # No necesitamos populate_by_name si los nombres coinciden


class MenuResponse(BaseModel):
    menu: List[MenuItem]

    class Config:
        from_attributes = True