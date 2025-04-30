# app/schemas/area.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Schemas Base, Create, Update ---
class AreaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    es_activo: bool = True

class AreaCreate(AreaBase):
    pass

class AreaUpdate(BaseModel):
    # Todos los campos son opcionales en la actualización
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    es_activo: Optional[bool] = None

# --- Schema de Lectura (para devolver datos) ---
class AreaRead(AreaBase):
    area_id: int
    fecha_creacion: datetime

class AreaSimpleList(BaseModel):
    area_id: int
    nombre: str

    # Para Pydantic V1:
    # class Config:
    #     orm_mode = True
    # Para Pydantic V2 (recomendado):
    model_config = {
        "from_attributes": True
    }


# --- Schema para la Respuesta Paginada ---
class PaginatedAreaResponse(BaseModel):
    areas: List[AreaRead]
    total_areas: int
    pagina_actual: int
    total_paginas: int


