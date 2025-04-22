# app/api/v1/endpoints/menus.py (CORREGIDO OTRA VEZ)

from fastapi import APIRouter, HTTPException, Depends
from app.db.queries import execute_procedure
# 1. Importa build_menu_tree (y create_menu_response si la usas)
from app.utils.menu_helper import build_menu_tree #, create_menu_response
from app.core.logging_config import get_logger
# 2. Importa SOLO MenuResponse (MenuItem se usa dentro del helper)
from app.schemas.menu import MenuResponse #, MenuItem

# (Opcional) Importa dependencias de autenticación si es necesario
# from app.api.deps import get_current_active_user
# from app.schemas.usuario import Usuario

router = APIRouter()
logger = get_logger(__name__)

@router.get("/getmenu", response_model=MenuResponse)
async def get_menu(
    # Opcional: Añade dependencia si necesitas el usuario actual
    # current_user: Usuario = Depends(get_current_active_user)
):
    """
    Endpoint para construir Menus. Devuelve la estructura { "menu": [...] }.
    Utiliza menu_helper para construir el árbol desde datos crudos.
    """
    procedure_name = "sp_GetFullMenu"

    try:
        resultado = execute_procedure(procedure_name)
        if not resultado:
            logger.warning("No se encontraron menús en sp_GetFullMenu.")
            return MenuResponse(menu=[])

        # 3. Obtener la lista de diccionarios crudos
        menu_items_raw = [dict(row) for row in resultado]

        # --- CAMBIO PRINCIPAL AQUÍ ---
        # 4. Pasar la lista de diccionarios crudos a build_menu_tree
        # Ya no necesitamos validar a MenuItem aquí, el helper lo hace.
        # try:
        #     menu_items_validated = [MenuItem(**item) for item in menu_items_raw]
        # except Exception as validation_error:
        #      ... (código de validación eliminado) ...

        # Llama a build_menu_tree con los datos crudos (diccionarios)
        menu_tree = build_menu_tree(menu_items_raw)
        # --- FIN DEL CAMBIO ---

        # 5. Devolver la respuesta usando el árbol construido
        return MenuResponse(menu=menu_tree)

        # Alternativa si usas create_menu_response:
        # return create_menu_response(menu_items_raw)


    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # Loguear el error que ocurre DENTRO de build_menu_tree si falla
        logger.exception(f"Error inesperado durante la obtención o construcción del menú: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al procesar el menú."
        )