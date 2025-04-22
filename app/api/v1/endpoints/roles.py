# app/api/v1/endpoints/roles.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any # Añadir Dict, Any

# Importar Schemas
from app.schemas.rol import RolCreate, RolUpdate, RolRead

# Importar Servicio
from app.services.rol_service import RolService

# Importar Excepciones personalizadas
from app.core.exceptions import ServiceError, ValidationError

# --- Importar Dependencias de Autorización ---
from app.api.deps import get_current_active_user, RoleChecker

# Logging
from app.core.logging_config import get_logger
logger = get_logger(__name__)

router = APIRouter()

# --- Dependencia específica para requerir rol 'admin' ---
require_admin = RoleChecker(["admin"])

# --- Endpoint para Crear Roles ---
@router.post(
    "/",
    response_model=RolRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo rol",
    description="Crea un nuevo rol en el sistema. **Requiere rol 'admin'.**",
    dependencies=[Depends(require_admin)] # Aplicar dependencia de rol
)
async def create_rol(
    rol_in: RolCreate,
    # current_user: Dict[str, Any] = Depends(get_current_active_user) # Opcional si necesitas info del admin que crea
):
    """
    Crea un nuevo rol con los datos proporcionados.
    - **nombre**: Nombre único del rol (obligatorio).
    - **descripcion**: Descripción opcional del rol.
    - **es_activo**: Estado inicial del rol (por defecto True).
    """
    try:
        rol_dict = rol_in.model_dump()
        created_rol = await RolService.crear_rol(rol_data=rol_dict)
        return created_rol
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint create_rol: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al crear el rol.")

# --- Endpoint para Listar Roles ---
@router.get(
    "/",
    response_model=List[RolRead],
    summary="Obtener lista de roles",
    description="Obtiene una lista paginada de roles. Puede filtrarse por estado activo. **Requiere autenticación.**",
    # Aplicar dependencia de usuario activo (cualquier rol)
    dependencies=[Depends(get_current_active_user)]
)
async def read_roles(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Número máximo de registros a devolver"),
    activos_only: bool = Query(False, description="Filtrar para obtener solo roles activos")
    # current_user: Dict[str, Any] = Depends(get_current_active_user) # Ya está en dependencies
):
    """
    Devuelve una lista de roles.
    - **skip**: Offset para paginación.
    - **limit**: Límite de resultados por página.
    - **activos_only**: Si es True, solo devuelve roles con `es_activo = true`.
    """
    try:
        roles = await RolService.obtener_roles(skip=skip, limit=limit, activos_only=activos_only)
        return roles
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint read_roles: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al obtener roles.")

# --- Endpoint para Obtener un Rol por ID ---
@router.get(
    "/{rol_id}",
    response_model=RolRead,
    summary="Obtener un rol por ID",
    description="Obtiene los detalles de un rol específico por su ID. **Requiere autenticación.**",
    # Aplicar dependencia de usuario activo (cualquier rol)
    dependencies=[Depends(get_current_active_user)]
)
async def read_rol(
    rol_id: int
    # current_user: Dict[str, Any] = Depends(get_current_active_user) # Ya está en dependencies
):
    """
    Devuelve los detalles del rol con el ID especificado.
    """
    try:
        rol = await RolService.obtener_rol_por_id(rol_id=rol_id)
        if rol is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
        return rol
    except ServiceError as e:
        logger.error(f"Error de servicio obteniendo rol ID {rol_id}: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint read_rol (ID: {rol_id}): {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al obtener el rol.")


# --- Endpoint para Actualizar un Rol ---
@router.put(
    "/{rol_id}",
    response_model=RolRead,
    summary="Actualizar un rol",
    description="Actualiza los datos de un rol existente. **Requiere rol 'admin'.**",
    dependencies=[Depends(require_admin)] # Aplicar dependencia de rol
)
async def update_rol(
    rol_id: int,
    rol_in: RolUpdate
    # current_user: Dict[str, Any] = Depends(get_current_active_user) # Opcional
):
    """
    Actualiza un rol existente.
    - **rol_id**: ID del rol a actualizar.
    - **rol_in**: Objeto con los campos a actualizar (nombre, descripcion, es_activo).
                 Solo se actualizarán los campos proporcionados.
    """
    try:
        update_data = rol_in.model_dump(exclude_unset=True)
        if not update_data:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron datos para actualizar."
            )

        updated_rol = await RolService.actualizar_rol(rol_id=rol_id, rol_data=update_data)
        return updated_rol
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint update_rol (ID: {rol_id}): {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al actualizar el rol.")

# --- Endpoint para Desactivar un Rol (Borrado Lógico) ---
@router.delete(
    "/{rol_id}",
    response_model=RolRead, # Devuelve el rol actualizado (inactivo)
    summary="Desactivar un rol",
    description="Marca un rol como inactivo (borrado lógico). **Requiere rol 'admin'.**",
    dependencies=[Depends(require_admin)] # Aplicar dependencia de rol
)
async def deactivate_rol(
    rol_id: int
    # current_user: Dict[str, Any] = Depends(get_current_active_user) # Opcional
):
    """
    Desactiva el rol con el ID especificado. El rol no se elimina permanentemente.
    """
    try:
        deactivated_rol = await RolService.desactivar_rol(rol_id=rol_id)
        return deactivated_rol
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint deactivate_rol (ID: {rol_id}): {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al desactivar el rol.")