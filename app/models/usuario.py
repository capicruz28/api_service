from typing import Optional
from pydantic import BaseModel

class UsuarioBase(BaseModel):
    cusuar: str
    ctraba: str
    estado: str

    class Config:
        from_attributes = True

class UsuarioCreate(UsuarioBase):
    cclave: str

class UsuarioUpdate(UsuarioBase):
    cclave: Optional[str] = None

class UsuarioLogin(BaseModel):
    cusuar: str
    cclave: str

class Usuario(UsuarioBase):
    id: int

    class Config:
        from_attributes = True