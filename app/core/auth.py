from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.security import verify_password
from app.db.queries import execute_auth_query
from app.schemas.auth import TokenPayload
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def create_access_token(data: dict) -> str:
    """
    Crea un token JWT con los datos proporcionados
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def authenticate_user(username: str, password: str) -> Dict:
    """
    Autentica un usuario y retorna sus datos si las credenciales son correctas
    """
    try:
        query = """
        SELECT usuario_id, nombre_usuario, correo, contrasena,
               nombre, apellido, es_activo
        FROM usuario
        WHERE nombre_usuario = ? AND es_eliminado = 0
        """
        user = execute_auth_query(query, (username,))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        if not verify_password(password, user['contrasena']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        if not user['es_activo']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo"
            )

        # Actualizar fecha último acceso
        update_query = """
        UPDATE usuario
        SET fecha_ultimo_acceso = GETDATE()
        WHERE usuario_id = ?
        """
        execute_auth_query(update_query, (user['usuario_id'],))

        # Eliminar la contraseña del resultado
        del user['contrasena']
        return user

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error en autenticación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de autenticación"
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Obtiene el usuario actual basado en el token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenPayload(username=username)
    except JWTError:
        raise credentials_exception

    query = """
    SELECT usuario_id, nombre_usuario, correo, nombre, apellido, es_activo
    FROM usuario
    WHERE nombre_usuario = ? AND es_eliminado = 0
    """
    user = execute_auth_query(query, (token_data.username,))

    if not user:
        raise credentials_exception
    return user