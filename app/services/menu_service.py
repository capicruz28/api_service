# app/services/menu_service.py

from typing import List, Dict, Optional # Añadir Optional
# Añadir execute_query
from app.db.queries import execute_procedure, execute_query, GET_ALL_MENUS_ADMIN
from app.core.exceptions import ServiceError
from app.utils.menu_helper import build_menu_tree # Asumiendo que existe este helper
from app.schemas.menu import MenuResponse, MenuItem # Importar schemas necesarios
import logging

logger = logging.getLogger(__name__)

class MenuService:
    @staticmethod
    async def get_full_menu() -> List[Dict]:
        """Obtiene el menú completo y lo estructura en árbol."""
        try:
            procedure_name = "sp_GetFullMenu"
            # Asumiendo que execute_procedure devuelve una lista de diccionarios planos
            resultado = execute_procedure(procedure_name)

            if not resultado:
                return []

            # Asumiendo que build_menu_tree toma la lista plana y la anida
            return build_menu_tree(resultado)
        except Exception as e:
            logger.error(f"Error obteniendo menú completo: {str(e)}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error obteniendo menú completo: {str(e)}")

    @staticmethod
    async def obtener_menu_por_id(menu_id: int) -> Optional[Dict]:
        """
        Obtiene los detalles de un menú específico por su ID.
        Usa los nombres de columna de la tabla 'menu'.
        Devuelve None si no se encuentra o no está activo.
        """
        try:
            # --- USA LOS NOMBRES CORRECTOS DE TU TABLA 'menu' ---
            query = """
            SELECT menu_id, nombre, icono, ruta, padre_menu_id, orden, es_activo
            FROM menu
            WHERE menu_id = ?
            """
            resultados = execute_query(query, (menu_id,))

            if not resultados:
                logger.debug(f"Menú con ID {menu_id} no encontrado.")
                return None

            menu_data = resultados[0]

            # Verificar si está activo
            if not menu_data.get('es_activo', False): # Usar .get por seguridad
                 logger.debug(f"Menú con ID {menu_id} encontrado pero está inactivo.")
                 return None # No devolver menús inactivos

            logger.debug(f"Menú con ID {menu_id} encontrado y activo.")
            # Asumiendo que tus Schemas Pydantic usan estos mismos nombres (menu_id, nombre, etc.)
            return menu_data

        except Exception as e:
            logger.error(f"Error obteniendo menú por ID {menu_id}: {str(e)}", exc_info=True)
            return None # Devolver None en caso de error

    @staticmethod
    async def obtener_todos_menus_estructurados_admin() -> MenuResponse:
        """
        Obtiene TODOS los elementos del menú (activos e inactivos) de forma asíncrona
        y los devuelve en una estructura de árbol jerárquica.
        Utiliza la stored procedure sp_GetAllMenuItemsAdmin.

        Returns:
            MenuResponse: Objeto que contiene la lista jerárquica de menús.

        Raises:
            ServiceError: Si ocurre un error durante la consulta o el procesamiento.
        """
        logger.info("Obteniendo estructura completa de menús para admin.")
        try:
            # Llamada directa a la función de queries
            # Asumiendo que execute_procedure devuelve lista de pyodbc.Row o similar
            resultado_sp = execute_procedure(GET_ALL_MENUS_ADMIN) # GET_ALL_MENUS_ADMIN es solo el nombre

            if not resultado_sp:
                logger.warning("sp_GetAllMenuItemsAdmin no devolvió resultados.")
                return MenuResponse(menu=[])

            # Convertir a lista de diccionarios para build_menu_tree
            menu_items_raw = [dict(row) for row in resultado_sp]
            menu_tree: List[MenuItem] = build_menu_tree(menu_items_raw)

            logger.info(f"Estructura de menú admin construida con {len(menu_tree)} items raíz.")
            return MenuResponse(menu=menu_tree)

        # --- CAPTURAR DatabaseError PRIMERO (SI APLICA) ---
        except DatabaseError as db_error:
             logger.error(f"Error de base de datos al obtener estructura admin: {db_error}", exc_info=True)
             # Lanzar ServiceError consistente
             raise ServiceError(status_code=500, detail=f"Error de base de datos al obtener estructura admin: {db_error.detail}")
        # --- CAPTURAR Exception GENERAL DESPUÉS ---
        except Exception as e:
            logger.exception(f"Error inesperado al obtener/construir el árbol de menús admin: {e}")
            # Lanzar ServiceError consistente
            raise ServiceError(
                status_code=500, # O un código más específico si lo deseas
                detail="Error interno al procesar la estructura completa del menú."
            )