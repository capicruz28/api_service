from typing import List, Dict
from app.db.queries import execute_procedure
from app.core.exceptions import ServiceError
from app.utils.menu_helper import build_menu_tree
import logging

logger = logging.getLogger(__name__)

class MenuService:
    @staticmethod
    async def get_full_menu() -> List[Dict]:
        try:
            procedure_name = "sp_GetFullMenu"
            resultado = execute_procedure(procedure_name)

            if not resultado:
                return []

            return build_menu_tree(resultado)
        except Exception as e:
            logger.error(f"Error obteniendo menú: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo menú: {str(e)}")