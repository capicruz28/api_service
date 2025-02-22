from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import Token, LoginData
from app.core.auth import authenticate_user, create_access_token
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/login", response_model=Token)
async def login(login_data: LoginData):
    """
    Endpoint para autenticar usuarios y generar token JWT
    """
    try:
        user = await authenticate_user(login_data.username, login_data.password)

        access_token = create_access_token(
            data={"sub": user["nombre_usuario"]}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": user
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de login"
        )