from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class EmpleadoBase(BaseModel):
    ctraba: str
    nombre: str
    apellido: str
    fecha_ingreso: datetime
    estado: str
    cargo: Optional[str] = None

    class Config:
        from_attributes = True

class EmpleadoCreate(EmpleadoBase):
    pass

class EmpleadoUpdate(EmpleadoBase):
    pass

class Empleado(EmpleadoBase):
    id: int

    class Config:
        from_attributes = True