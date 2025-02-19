from fastapi import APIRouter, HTTPException
from app.db.queries import execute_procedure
from app.utils.menu_helper import build_menu_tree
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/getmenu")
async def get_menu():
    procedure_name = "sp_GetFullMenu"

    try:
        resultado = execute_procedure(procedure_name)
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron menús"
            )

        # Convertir los resultados a una lista de diccionarios
        menu_items = [dict(row) for row in resultado]

        # Construir el árbol de menú
        menu_tree = build_menu_tree(menu_items)

        return {"data": menu_tree}
    except Exception as e:
        logger.error(f"Error al obtener menú: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en el servidor: {str(e)}"
        )