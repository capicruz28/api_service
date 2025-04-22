# app/api/v1/endpoints/auth.py (CORREGIDO PARA SWAGGER AUTH)

from fastapi import APIRouter, HTTPException, status, Depends
# --- IMPORTAR OAuth2PasswordRequestForm ---
from fastapi.security import OAuth2PasswordRequestForm
# Asegúrate que UserDataWithRoles espere 'roles: List[str]'
# Ya no necesitas LoginData aquí para la entrada
from app.schemas.auth import Token, UserDataWithRoles # Quitar LoginData si no se usa en otro lado
from app.core.auth import authenticate_user, create_access_token
from app.core.logging_config import get_logger
# --- IMPORTAR EL SERVICIO DE USUARIO ---
from app.services.usuario_service import UsuarioService

router = APIRouter()
logger = get_logger(__name__)

# --- FUNCIÓN PARA OBTENER EL SERVICIO (si usas Depends) ---
# def get_usuario_service():
#     yield UsuarioService()

@router.post(
    "/login",
    response_model=Token, # Token debe contener UserDataWithRoles con roles: List[str]
    summary="Autenticar usuario y obtener token",
    description="Verifica las credenciales del usuario, obtiene sus datos y nombres de roles, y genera un token JWT."
)
async def login(
    # --- CAMBIAR login_data: LoginData POR form_data: OAuth2PasswordRequestForm ---
    form_data: OAuth2PasswordRequestForm = Depends(),
    # usuario_service: UsuarioService = Depends(get_usuario_service) # Descomentar si usas Depends
):
    """
    Endpoint para autenticar usuarios, obtener sus datos (incluyendo nombres de roles)
    y generar token JWT. Acepta credenciales como form data (username, password).
    """
    # --- Instanciar servicio si NO usas Depends ---
    usuario_service = UsuarioService() # Comentar si usas Depends

    try:
        # 1. Autenticar al usuario usando form_data
        # --- USAR form_data.username y form_data.password ---
        user_base_data = await authenticate_user(form_data.username, form_data.password)
        if not user_base_data:
             logger.warning(f"authenticate_user devolvió None para el usuario {form_data.username}")
             raise HTTPException(
                 status_code=status.HTTP_401_UNAUTHORIZED,
                 detail="Credenciales incorrectas o usuario no encontrado",
                 headers={"WWW-Authenticate": "Bearer"},
             )

        # 2. Obtener el ID del usuario
        user_id = user_base_data.get('usuario_id')
        if not user_id:
            logger.error(f"Los datos base del usuario {form_data.username} no contienen 'usuario_id'. Datos: {user_base_data}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno: No se pudo obtener el ID del usuario autenticado."
            )

        # 3. Obtener los NOMBRES de roles del usuario usando el servicio
        try:
            user_role_names = await usuario_service.get_user_role_names(user_id=user_id)
            logger.info(f"Nombres de roles obtenidos para usuario ID {user_id}: {user_role_names}")
        except Exception as service_error:
            logger.exception(f"Error al obtener nombres de roles para usuario ID {user_id} desde UsuarioService: {service_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno: No se pudieron obtener los roles del usuario."
            )

        # 4. Combinar datos base y nombres de roles
        user_full_data = {**user_base_data, "roles": user_role_names}

        # 5. Crear el token JWT (usando form_data.username como 'sub')
        access_token = create_access_token(
            # --- USAR form_data.username ---
            data={"sub": form_data.username}
            # Si necesitas roles en el payload del token:
            # data={"sub": form_data.username, "roles": user_role_names}
        )

        # 6. Devolver la respuesta completa
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": user_full_data # Validado por response_model
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # --- USAR form_data.username en el log ---
        logger.exception(f"Error inesperado en el endpoint /login para usuario {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado durante el proceso de login."
        )