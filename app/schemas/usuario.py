from pydantic import BaseModel, Field
from typing import Optional, List

class UsuarioBase(BaseModel):
    cusuar: str = Field(..., min_length=2, description="Código de usuario")
    cclave: str = Field(..., min_length=2, description="Contraseña del usuario")

class UsuarioResponse(BaseModel):
    data: List[dict]
    message: str = "Success"

class LoginRequest(BaseModel):
    cusuar: str = Field(..., min_length=2)
    cclave: str = Field(..., min_length=2)