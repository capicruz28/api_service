from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class EmpleadoBase(BaseModel):
    ctraba: str = Field(..., min_length=2, description="Código del trabajador")
    nordpr: str = Field(..., min_length=5, max_length=6, description="Número de orden")
    ccarub: Optional[str] = Field(None, description="Código de cargo")

class EmpleadoResponse(BaseModel):
    data: List[dict]
    message: str = "Success"

class PlanCuotasResponse(BaseModel):
    data: List[dict]
    message: str = "Success"

class EmpleadoBusquedaParams(BaseModel):
    nordpr: str = Field(..., min_length=5, max_length=6)
    ccarub: Optional[str] = None