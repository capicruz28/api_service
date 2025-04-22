# app/api/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import List, Dict, Any

from app.core.config import settings
from app.core.auth import oauth2_scheme # Reutilizamos el scheme definido
from app.db.queries import execute_auth_query, execute_query # Necesitamos acceso a queries
from app.schemas.auth import TokenPayload
from app.services.usuario_service import UsuarioService # Para obtener roles

import logging
logger = logging.getLogger(__name__)

# Excepción estándar para credenciales inválidas
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)

# Excepción para usuario inactivo
inactive_user_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, # 403 Forbidden es más apropiado que 401
    detail="Usuario inactivo",
)

# Excepción para permisos insuficientes
forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Permisos insuficientes",
)


async def get_current_user_data(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Decodifica el token, obtiene el nombre de usuario y lo devuelve.
    No accede a la base de datos aquí para optimizar.
    Lanza excepción si el token es inválido o ha expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token JWT inválido: falta 'sub'.")
            raise credentials_exception
        # Podríamos añadir más validaciones del payload aquí si fuera necesario
        # Por ejemplo, verificar un 'token_type' si lo incluimos en el payload.

        # Devolvemos el payload decodificado o solo el username/token_data
        # Devolver el payload puede ser útil si añadimos más datos al token en el futuro
        return payload # Contiene 'sub' y 'exp'

    except JWTError as e:
        logger.warning(f"Error de validación JWT: {e}")
        raise credentials_exception


async def get_current_active_user(
    payload: Dict[str, Any] = Depends(get_current_user_data)
) -> Dict[str, Any]:
    """
    Dependencia principal: Obtiene los datos completos del usuario activo desde la BD
    basado en el nombre de usuario del token y añade sus roles.
    """
    username = payload.get("sub")
    # No necesitamos verificar username is None aquí, get_current_user_data ya lo hizo

    try:
        # Obtener datos básicos del usuario
        user_query = """
        SELECT usuario_id, nombre_usuario, correo, nombre, apellido, es_activo
        FROM usuario
        WHERE nombre_usuario = ? AND es_eliminado = 0
        """
        user = execute_auth_query(user_query, (username,))

        if not user:
            logger.warning(f"Usuario '{username}' del token válido no encontrado en BD (o eliminado).")
            raise credentials_exception # El usuario ya no existe

        # ¡Verificar si el usuario está activo!
        if not user.get('es_activo'):
            logger.warning(f"Usuario '{username}' autenticado pero inactivo.")
            raise inactive_user_exception

        # Obtener roles del usuario usando el servicio
        # Usamos try-except aquí por si falla la obtención de roles,
        # aunque no debería fallar si el usuario existe.
        try:
            roles_list = await UsuarioService.obtener_roles_de_usuario(user['usuario_id'])
            # Extraer solo los nombres de los roles para facilitar las comprobaciones
            user['roles'] = [rol['nombre'] for rol in roles_list]
        except Exception as role_error:
            logger.error(f"Error obteniendo roles para usuario ID {user['usuario_id']}: {role_error}")
            # Decidir si fallar o continuar sin roles. Es más seguro fallar.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al obtener roles del usuario."
            )

        logger.debug(f"Usuario activo '{username}' (ID: {user['usuario_id']}) obtenido con roles: {user['roles']}")
        return user # Devuelve el diccionario del usuario con la clave 'roles' añadida

    except HTTPException as e:
        # Re-lanzar excepciones HTTP ya manejadas (credentials, inactive)
        raise e
    except Exception as e:
        logger.error(f"Error inesperado obteniendo usuario activo '{username}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el usuario."
        )


# --- Dependencia de Autorización por Rol ---

class RoleChecker:
    """
    Clase para crear dependencias que verifican roles específicos.
    Permite pasar el rol requerido al crear la dependencia.
    Ejemplo de uso en un endpoint: Depends(RoleChecker(["admin", "manager"]))
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: Dict[str, Any] = Depends(get_current_active_user)):
        """
        Verifica si alguno de los roles del usuario actual está en la lista de roles permitidos.
        """
        user_roles = current_user.get("roles", [])
        logger.debug(f"Verificando roles. Usuario: {current_user.get('nombre_usuario')}, Roles: {user_roles}, Roles requeridos: {self.allowed_roles}")

        # Comprobar si hay alguna intersección entre los roles del usuario y los permitidos
        if not any(role in self.allowed_roles for role in user_roles):
            logger.warning(f"Acceso denegado para usuario '{current_user.get('nombre_usuario')}'. Roles: {user_roles}. Roles requeridos: {self.allowed_roles}")
            raise forbidden_exception # Lanzar 403 Forbidden

        logger.debug(f"Acceso permitido para usuario '{current_user.get('nombre_usuario')}' basado en roles.")
        # No necesitamos devolver nada, si no hay excepción, el acceso está permitido.
        # Podríamos devolver el usuario si fuera útil en el endpoint: return current_user