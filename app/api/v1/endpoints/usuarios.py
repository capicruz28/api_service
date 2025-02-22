from fastapi import APIRouter, HTTPException
from app.schemas.usuario import UsuarioCreate, UsuarioResponse
from app.services.usuario_service import UsuarioService
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/", response_model=UsuarioResponse)
async def crear_usuario(usuario: UsuarioCreate):
    """
    Crea un nuevo usuario
    """
    try:
        usuario_dict = usuario.model_dump()
        result = await UsuarioService.crear_usuario(usuario_dict)
        return result
    except Exception as e:
        logger.error(f"Error creando usuario: {str(e)}")
        if hasattr(e, 'status_code'):
            raise HTTPException(
                status_code=e.status_code,
                detail=str(e.detail)
            )
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
