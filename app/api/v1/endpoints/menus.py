# app/api/v1/endpoints/menus.py

# --- Importaciones Existentes ---
from fastapi import APIRouter, HTTPException, Depends, status, Body
from app.db.queries import execute_procedure
from app.utils.menu_helper import build_menu_tree
from app.core.logging_config import get_logger
from app.api.deps import get_current_active_user, RoleChecker
from typing import List, Dict, Any
from app.services.menu_service import MenuService
from app.schemas.menu import (
    MenuResponse, MenuCreate, MenuUpdate, MenuReadSingle, MenuItem
)
# --- Importaciones de Excepciones CORREGIDAS ---
# Solo importamos ServiceError (y DatabaseError si la usas y existe)
from app.core.exceptions import ServiceError #, DatabaseError # Descomenta si existe y la usas
# --- FIN CORRECCIÓN IMPORTACIONES ---

# (Opcional) Importa Usuario si lo usas en alguna dependencia
# from app.schemas.usuario import Usuario

router = APIRouter()
logger = get_logger(__name__)

ADMIN_ROLE_CHECK = Depends(RoleChecker(["Administrador"]))

# --- Endpoint Existente: /getmenu ---
@router.get("/getmenu", response_model=MenuResponse)
async def get_menu(
    # current_user: Usuario = Depends(get_current_active_user)
):
    procedure_name = "sp_GetFullMenu"
    logger.info(f"Solicitud recibida en GET /menus/getmenu (llamando a {procedure_name})")
    try:
        resultado = execute_procedure(procedure_name)
        if not resultado:
            logger.warning(f"No se encontraron menús en {procedure_name}.")
            return MenuResponse(menu=[])
        menu_items_raw = [dict(row) for row in resultado]
        menu_tree = build_menu_tree(menu_items_raw)
        return MenuResponse(menu=menu_tree)
    except ServiceError as se: # Captura ServiceError directamente
        logger.error(f"Error de servicio en GET /getmenu: {se.detail}")
        raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception(f"Error inesperado durante la obtención/construcción del menú de usuario: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al procesar el menú de usuario."
        )

# --- Endpoint Existente: /all-structured ---
@router.get(
    "/all-structured",
    response_model=MenuResponse,
    summary="Obtener Árbol Completo de Menús (Admin)",
    description="Obtiene todos los elementos del menú (activos e inactivos) estructurados jerárquicamente. Requiere rol 'Administrador'.",
    dependencies=[ADMIN_ROLE_CHECK]
)
async def get_all_menus_admin_structured_endpoint():
    logger.info("Solicitud recibida en GET /menus/all-structured (Admin)")
    try:
        response = await MenuService.obtener_todos_menus_estructurados_admin()
        return response
    except ServiceError as se: # Captura ServiceError directamente
         logger.error(f"Error de servicio en GET /menus/all-structured: {se.detail}")
         raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception("Error inesperado en el endpoint /menus/all-structured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la estructura completa del menú."
        )

# --- NUEVO: Endpoint para Crear Menú ---
@router.post(
    "/",
    response_model=MenuReadSingle,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo ítem de menú (Admin)",
    dependencies=[ADMIN_ROLE_CHECK]
)
async def create_menu_endpoint(
    menu_in: MenuCreate = Body(...)
):
    logger.info(f"Recibida solicitud POST /menus/ para crear menú: {menu_in.nombre}")
    try:
        created_menu = await MenuService.crear_menu(menu_in)
        return created_menu
    except ServiceError as se: # Captura ServiceError directamente
        logger.warning(f"Error de servicio (posible validación) al crear menú: {se.detail}")
        # Usa el status_code de la excepción del servicio (puede ser 400 o 500)
        raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception("Error inesperado en endpoint POST /menus/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear menú.")

# --- NUEVO: Endpoint para Obtener Menú por ID ---
@router.get(
    "/{menu_id}",
    response_model=MenuReadSingle,
    summary="Obtener detalles de un ítem de menú por ID (Admin)",
    dependencies=[ADMIN_ROLE_CHECK]
)
async def get_menu_by_id_endpoint(menu_id: int):
    logger.debug(f"Recibida solicitud GET /menus/{menu_id}")
    try:
        menu = await MenuService.obtener_menu_por_id(menu_id)
        if menu is None:
            # Si el servicio devuelve None, lanzamos 404 aquí
            logger.warning(f"Menú con ID {menu_id} no encontrado (servicio devolvió None).")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menú no encontrado")
        return menu
    except ServiceError as se: # Captura ServiceError si el servicio lo lanza
        logger.error(f"Error de servicio obteniendo menú {menu_id}: {se.detail}")
        raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception(f"Error inesperado obteniendo menú {menu_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener menú.")


# --- NUEVO: Endpoint para Actualizar Menú ---
@router.put(
    "/{menu_id}",
    response_model=MenuReadSingle,
    summary="Actualizar un ítem de menú existente (Admin)",
    dependencies=[ADMIN_ROLE_CHECK]
)
async def update_menu_endpoint(
    menu_id: int,
    menu_in: MenuUpdate = Body(...)
):
    logger.info(f"Recibida solicitud PUT /menus/{menu_id}")
    update_data = menu_in.model_dump(exclude_unset=True)
    if not update_data:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El cuerpo de la solicitud no puede estar vacío para actualizar.")
    try:
        updated_menu = await MenuService.actualizar_menu(menu_id, menu_in)
        return updated_menu
    except ServiceError as se: # Captura ServiceError directamente (puede ser 404, 400, 500)
        logger.warning(f"Error de servicio al actualizar menú {menu_id}: {se.detail}")
        raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint PUT /menus/{menu_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar menú.")

# --- NUEVO: Endpoint para Desactivar Menú (Borrado Lógico) ---
@router.delete(
    "/{menu_id}",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any],
    summary="Desactivar un ítem de menú (Borrado Lógico) (Admin)",
    dependencies=[ADMIN_ROLE_CHECK]
)
async def deactivate_menu_endpoint(menu_id: int):
    logger.info(f"Recibida solicitud DELETE /menus/{menu_id}")
    try:
        result = await MenuService.desactivar_menu(menu_id)
        return {"message": f"Menú ID {result.get('menu_id')} desactivado exitosamente.", "menu_id": result.get('menu_id'), "es_activo": result.get('es_activo')}
    except ServiceError as se: # Captura ServiceError directamente (puede ser 404, 400, 500)
        logger.warning(f"No se pudo desactivar menú {menu_id}: {se.detail}")
        raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint DELETE /menus/{menu_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al desactivar menú.")

# --- NUEVO (Opcional): Endpoint para Reactivar Menú ---
@router.put(
    "/{menu_id}/reactivate",
    response_model=Dict[str, Any],
    summary="Reactivar un ítem de menú desactivado (Admin)",
    dependencies=[ADMIN_ROLE_CHECK]
)
async def reactivate_menu_endpoint(menu_id: int):
    logger.info(f"Recibida solicitud PUT /menus/{menu_id}/reactivate")
    try:
        result = await MenuService.reactivar_menu(menu_id)
        return {"message": f"Menú ID {result.get('menu_id')} reactivado exitosamente.", "menu_id": result.get('menu_id'), "es_activo": result.get('es_activo')}
    except ServiceError as se: # Captura ServiceError directamente (puede ser 404, 500)
        logger.warning(f"No se pudo reactivar menú {menu_id}: {se.detail}")
        raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint PUT /menus/{menu_id}/reactivate")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al reactivar menú.")

@router.get(
    "/area/{area_id}/tree",
    response_model=MenuResponse, # Devuelve la misma estructura que los otros árboles
    summary="Obtener árbol de menú para un Área específica (Admin)",
    description="Obtiene la estructura jerárquica completa (activos e inactivos) de los menús pertenecientes a un área específica. Requiere rol 'Administrador'.",
    dependencies=[ADMIN_ROLE_CHECK]
)
async def get_menu_tree_by_area_endpoint(area_id: int):
    """Obtiene el árbol de menú filtrado por el ID del área proporcionado."""
    logger.info(f"Solicitud GET /menus/area/{area_id}/tree recibida.")
    try:
        # Llama al nuevo método del servicio
        menu_response = await MenuService.obtener_arbol_menu_por_area(area_id)
        # El servicio ya devuelve MenuResponse(menu=[]) si no hay menús
        return menu_response
    except ServiceError as se:
        logger.error(f"Error de servicio al obtener árbol de menú para área {area_id}: {se.detail}")
        raise HTTPException(status_code=se.status_code, detail=se.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint GET /menus/area/{area_id}/tree")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener el árbol de menú del área.")