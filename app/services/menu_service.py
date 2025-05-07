# app/services/menu_service.py

from typing import List, Dict, Optional, Any
# Asegúrate de importar todas las funciones y constantes de queries necesarias
from app.db.queries import (
    execute_procedure, execute_procedure_params, execute_query, execute_insert, execute_update,
    GET_ALL_MENUS_ADMIN, INSERT_MENU, SELECT_MENU_BY_ID, UPDATE_MENU_TEMPLATE,
    DEACTIVATE_MENU, REACTIVATE_MENU, CHECK_MENU_EXISTS, CHECK_AREA_EXISTS,
    GET_MENUS_BY_AREA_FOR_TREE_QUERY,GET_MAX_ORDEN_FOR_SIBLINGS, GET_MAX_ORDEN_FOR_ROOT
)
# --- SOLO IMPORTAMOS ServiceError (y DatabaseError si existe y se usa) ---
from app.core.exceptions import ServiceError #, DatabaseError # Descomenta DatabaseError si existe y la usas
from app.utils.menu_helper import build_menu_tree
# Importa los schemas necesarios
from app.schemas.menu import (
    MenuResponse, MenuItem, MenuCreate, MenuUpdate, MenuReadSingle
)
import logging

logger = logging.getLogger(__name__)

# --- ASUMIMOS QUE DatabaseError PUEDE O NO ESTAR DEFINIDA ---
# Si no está definida en tus excepciones, elimina el bloque 'except DatabaseError'
# o reemplázalo por 'except Exception'.
# Por coherencia con tu código original, lo mantendré donde estaba.
try:
    from app.core.exceptions import DatabaseError
except ImportError:
    DatabaseError = Exception # Si no existe, que capture Exception general en su lugar


class MenuService:

    @staticmethod
    async def get_menu_for_user(usuario_id: int) -> MenuResponse:
        """
        Obtiene la estructura de menú filtrada según los roles y permisos
        del usuario especificado.
        """
        procedure_name = "sp_GetMenuForUser"
        # --- CORRECCIÓN AQUÍ ---
        # Cambiar la clave para que coincida EXACTAMENTE con el parámetro del SP
        params_dict = {'UsuarioID': usuario_id} # <<< Clave corregida
        # --- FIN CORRECCIÓN ---

        logger.info(f"Obteniendo menú filtrado para usuario_id: {usuario_id} usando {procedure_name}")
        try:
            # Llamar a execute_procedure_params con el diccionario corregido
            resultado_sp = execute_procedure_params(procedure_name, params_dict)

            if not resultado_sp:
                logger.info(f"No se encontraron menús permitidos para el usuario ID: {usuario_id}.")
                # Devolver una respuesta vacía si el SP no devuelve nada
                return MenuResponse(menu=[])

            # execute_procedure_params ya devuelve una lista de diccionarios
            # menu_items_raw = [dict(row) for row in resultado_sp] # No es necesario si ya devuelve dicts

            # Usar el helper para construir el árbol con los datos filtrados
            menu_tree: List[MenuItem] = build_menu_tree(resultado_sp) # Pasar directamente resultado_sp
            logger.info(f"Árbol de menú construido para usuario {usuario_id} con {len(menu_tree)} items raíz.")

            return MenuResponse(menu=menu_tree)

        except DatabaseError as db_err: # Captura específica si existe
             logger.error(f"Error de DB al obtener menú para usuario {usuario_id}: {db_err}", exc_info=True)
             raise ServiceError(status_code=500, detail=f"Error DB al obtener menú del usuario: {getattr(db_err, 'detail', str(db_err))}")
        except Exception as e:
            logger.error(f"Error inesperado al obtener/construir árbol de menú para usuario {usuario_id}: {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="Error interno al procesar el menú del usuario.")

    # --- Métodos existentes (get_full_menu, obtener_menu_por_id) ---
    # (Los dejamos como estaban en tu código original, ya que no usaban las nuevas excepciones)
    @staticmethod
    async def get_full_menu() -> List[Dict]:
        """Obtiene el menú completo y lo estructura en árbol."""
        try:
            procedure_name = "sp_GetFullMenu"
            resultado = execute_procedure(procedure_name)
            if not resultado: return []
            return build_menu_tree(resultado)
        except Exception as e:
            logger.error(f"Error obteniendo menú completo: {str(e)}", exc_info=True)
            # Levanta ServiceError genérico como en tu código original
            raise ServiceError(status_code=500, detail=f"Error obteniendo menú completo: {str(e)}")

    @staticmethod
    async def obtener_menu_por_id(menu_id: int) -> Optional[MenuReadSingle]: # Cambiado a MenuReadSingle
        """Obtiene los detalles de un menú específico por su ID."""
        logger.debug(f"Buscando menú con ID: {menu_id}")
        try:
            # Usamos la query que incluye el nombre del área
            resultado = execute_query(SELECT_MENU_BY_ID, (menu_id,))
            if not resultado:
                logger.debug(f"Menú con ID {menu_id} no encontrado.")
                return None

            menu_data = resultado[0]

            # Verificar si está activo (si es necesario para este método)
            # if not menu_data.get('es_activo', False):
            #      logger.debug(f"Menú con ID {menu_id} encontrado pero está inactivo.")
            #      return None # O devolverlo si el admin puede ver inactivos aquí

            # Devolvemos el objeto validado por Pydantic
            return MenuReadSingle(**menu_data)
        # Manejo de errores como en tu código original (log y return None)
        except Exception as e: # Captura Exception general
            logger.error(f"Error obteniendo menú por ID {menu_id}: {str(e)}", exc_info=True)
            return None # Devolver None en caso de error

    # --- Método existente (obtener_todos_menus_estructurados_admin) ---
    # (Mantenemos el manejo de DatabaseError si existe, como en tu código)
    @staticmethod
    async def obtener_todos_menus_estructurados_admin() -> MenuResponse:
        logger.info("Obteniendo estructura completa de menús para admin.")
        try:
            resultado_sp = execute_procedure(GET_ALL_MENUS_ADMIN)
            if not resultado_sp:
                logger.warning(f"{GET_ALL_MENUS_ADMIN} no devolvió resultados.")
                return MenuResponse(menu=[])
            # execute_procedure ya devuelve lista de dicts
            # menu_items_raw = [dict(row) for row in resultado_sp]
            menu_tree: List[MenuItem] = build_menu_tree(resultado_sp)
            logger.info(f"Estructura de menú admin construida con {len(menu_tree)} items raíz.")
            return MenuResponse(menu=menu_tree)
        except DatabaseError as db_error: # Mantenemos captura específica si existe
             logger.error(f"Error de base de datos al obtener estructura admin: {db_error}", exc_info=True)
             raise ServiceError(status_code=500, detail=f"Error DB: {getattr(db_error, 'detail', str(db_error))}")
        except Exception as e:
            logger.exception(f"Error inesperado al obtener/construir el árbol de menús admin: {e}")
            raise ServiceError(status_code=500, detail="Error interno al procesar estructura menú.")


    # --- NUEVO: Crear Menú (Manejo de errores simplificado) ---
    @staticmethod
    async def crear_menu(menu_data: MenuCreate) -> MenuReadSingle:
        logger.info(f"Intentando crear menú: {menu_data.nombre}")
        try:
            # --- Validaciones Previas ---
            if menu_data.padre_menu_id:
                padre_exists = execute_query(CHECK_MENU_EXISTS, (menu_data.padre_menu_id,))
                if not padre_exists:
                    raise ServiceError(status_code=400, detail=f"El menú padre con ID {menu_data.padre_menu_id} no existe.")
            if not menu_data.area_id: # Asumimos que area_id es obligatorio
                 raise ServiceError(status_code=400, detail="El ID del área es obligatorio para crear un menú.")
            else:
                area_exists = execute_query(CHECK_AREA_EXISTS, (menu_data.area_id,))
                if not area_exists:
                     raise ServiceError(status_code=400, detail=f"El área con ID {menu_data.area_id} no existe.")

            # --- Calcular el siguiente 'orden' ---
            max_orden_result = None
            if menu_data.padre_menu_id:
                # Buscar max orden entre hermanos
                max_orden_result = execute_query(GET_MAX_ORDEN_FOR_SIBLINGS, (menu_data.area_id, menu_data.padre_menu_id))
            else:
                # Buscar max orden entre raíces del área
                max_orden_result = execute_query(GET_MAX_ORDEN_FOR_ROOT, (menu_data.area_id,))

            max_orden = 0 # Valor por defecto si no hay hermanos/raíces
            if max_orden_result and max_orden_result[0]['max_orden'] is not None:
                max_orden = max_orden_result[0]['max_orden']

            next_orden = max_orden + 1
            logger.debug(f"Calculado next_orden: {next_orden} para padre {menu_data.padre_menu_id} en area {menu_data.area_id}")

            # --- Preparar parámetros para INSERT ---
            # Usamos el 'next_orden' calculado, ignoramos menu_data.orden
            params = (
                menu_data.nombre,
                menu_data.icono,
                menu_data.ruta,
                menu_data.padre_menu_id,
                next_orden, # <<< Usar el orden calculado
                menu_data.area_id,
                menu_data.es_activo
            )

            # --- Ejecutar Inserción ---
            resultado = execute_insert(INSERT_MENU, params)
            if not resultado or 'menu_id' not in resultado: # Verificar que se devolvió el ID
                 raise ServiceError(status_code=500, detail="La inserción no devolvió el registro creado correctamente.")

            # --- Obtener nombre del área (opcional, para la respuesta) ---
            area_nombre = None
            if resultado.get('area_id'):
                 area_info = execute_query("SELECT nombre FROM area_menu WHERE area_id = ?", (resultado['area_id'],))
                 if area_info: area_nombre = area_info[0]['nombre']

            # --- Crear y devolver respuesta ---
            # Asegurarse que el 'orden' en la respuesta es el insertado
            created_menu = MenuReadSingle(**resultado, area_nombre=area_nombre)
            logger.info(f"Menú '{created_menu.nombre}' creado con ID: {created_menu.menu_id} y orden: {created_menu.orden}")
            return created_menu

        except DatabaseError as db_err:
            logger.error(f"Error de DB al crear menú: {db_err}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error DB al crear menú: {getattr(db_err, 'detail', str(db_err))}")
        except ServiceError as se:
             logger.warning(f"Error de servicio (validación) al crear menú: {se.detail}")
             raise se
        except Exception as e:
            logger.exception(f"Error inesperado al crear menú: {e}")
            raise ServiceError(status_code=500, detail=f"Error interno al crear menú: {str(e)}")

    # --- NUEVO: Actualizar Menú (Manejo de errores simplificado) ---
    @staticmethod
    async def actualizar_menu(menu_id: int, menu_data: MenuUpdate) -> MenuReadSingle:
        logger.info(f"Intentando actualizar menú ID: {menu_id}")

        update_payload = menu_data.model_dump(exclude_unset=True)
        if not update_payload:
             # Levanta ServiceError en lugar de BadRequestError
             raise ServiceError(status_code=400, detail="No se proporcionaron datos para actualizar.")

        # Verificar que el menú exista primero (usando el método que devuelve None en error)
        menu_existente = await MenuService.obtener_menu_por_id(menu_id)
        if not menu_existente:
            # Levanta ServiceError en lugar de NotFoundError
            raise ServiceError(status_code=404, detail=f"Menú con ID {menu_id} no encontrado para actualizar.")

        try:
            # Validación simple (podrías añadir más lógica si quieres)
            if 'padre_menu_id' in update_payload and update_payload['padre_menu_id'] is not None:
                if menu_id == update_payload['padre_menu_id']:
                     raise ServiceError(status_code=400, detail="Un menú no puede ser su propio padre.")
                padre_exists = execute_query(CHECK_MENU_EXISTS, (update_payload['padre_menu_id'],))
                if not padre_exists:
                    raise ServiceError(status_code=400, detail=f"El menú padre con ID {update_payload['padre_menu_id']} no existe.")
            if 'area_id' in update_payload and update_payload['area_id'] is not None:
                area_exists = execute_query(CHECK_AREA_EXISTS, (update_payload['area_id'],))
                if not area_exists:
                     raise ServiceError(status_code=400, detail=f"El área con ID {update_payload['area_id']} no existe.")

            params = (
                update_payload.get('nombre'), update_payload.get('icono'), update_payload.get('ruta'),
                update_payload.get('padre_menu_id'), update_payload.get('orden'),
                update_payload.get('area_id'), update_payload.get('es_activo'),
                menu_id
            )
            resultado = execute_update(UPDATE_MENU_TEMPLATE, params)
            if not resultado:
                 raise ServiceError(status_code=500, detail="La actualización no devolvió el registro actualizado.")

            area_nombre = None
            if resultado.get('area_id'):
                 area_info = execute_query("SELECT nombre FROM area_menu WHERE area_id = ?", (resultado['area_id'],))
                 if area_info: area_nombre = area_info[0]['nombre']

            updated_menu = MenuReadSingle(**resultado, area_nombre=area_nombre)
            logger.info(f"Menú ID: {menu_id} actualizado exitosamente.")
            return updated_menu

        except DatabaseError as db_err: # Mantenemos captura específica si existe
            logger.error(f"Error de DB al actualizar menú {menu_id}: {db_err}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error DB al actualizar: {getattr(db_err, 'detail', str(db_err))}")
        except ServiceError as se: # Captura los ServiceError de validación o no encontrado
             logger.warning(f"Error de servicio (posible validación) al actualizar menú {menu_id}: {se.detail}")
             raise se # Relanzar el ServiceError
        except Exception as e:
            logger.exception(f"Error inesperado al actualizar menú {menu_id}: {e}")
            raise ServiceError(status_code=500, detail=f"Error interno al actualizar menú: {str(e)}")

    # --- NUEVO: Eliminar Menú (Lógico - Manejo de errores simplificado) ---
    @staticmethod
    async def desactivar_menu(menu_id: int) -> Dict[str, Any]:
        logger.info(f"Intentando desactivar menú ID: {menu_id}")
        try:
            resultado = execute_update(DEACTIVATE_MENU, (menu_id,))
            if not resultado:
                # Verificar si existe (podría ya estar inactivo)
                menu_existente = execute_query(CHECK_MENU_EXISTS, (menu_id,))
                if not menu_existente:
                     # Levanta ServiceError en lugar de NotFoundError
                     raise ServiceError(status_code=404, detail=f"Menú con ID {menu_id} no encontrado para desactivar.")
                else:
                     # Existe pero ya estaba inactivo
                     logger.warning(f"Menú ID: {menu_id} no se desactivó (posiblemente ya inactivo).")
                     # Levanta ServiceError indicando la situación
                     raise ServiceError(status_code=400, detail=f"Menú con ID {menu_id} ya estaba inactivo.")

            logger.info(f"Menú ID: {menu_id} desactivado exitosamente.")
            return {"menu_id": resultado.get('menu_id'), "es_activo": resultado.get('es_activo')}

        except DatabaseError as db_err: # Mantenemos captura específica si existe
            logger.error(f"Error de DB al desactivar menú {menu_id}: {db_err}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error DB al desactivar: {getattr(db_err, 'detail', str(db_err))}")
        except ServiceError as se: # Captura el 404 o 400
             logger.warning(f"No se pudo desactivar menú {menu_id}: {se.detail}")
             raise se # Relanzar
        except Exception as e:
            logger.exception(f"Error inesperado al desactivar menú {menu_id}: {e}")
            raise ServiceError(status_code=500, detail=f"Error interno al desactivar menú: {str(e)}")

    # --- (Opcional) Reactivar Menú (Manejo de errores simplificado) ---
    @staticmethod
    async def reactivar_menu(menu_id: int) -> Dict[str, Any]:
        logger.info(f"Intentando reactivar menú ID: {menu_id}")
        try:
            resultado = execute_update(REACTIVATE_MENU, (menu_id,))
            if not resultado:
                 # Levanta ServiceError en lugar de NotFoundError
                 raise ServiceError(status_code=404, detail=f"Menú con ID {menu_id} no encontrado o ya estaba activo.")

            logger.info(f"Menú ID: {menu_id} reactivado exitosamente.")
            return {"menu_id": resultado.get('menu_id'), "es_activo": resultado.get('es_activo')}
        except DatabaseError as db_err: # Mantenemos captura específica si existe
             raise ServiceError(status_code=500, detail=f"Error DB al reactivar: {getattr(db_err, 'detail', str(db_err))}")
        except ServiceError as se: # Captura el 404
             raise se # Relanzar
        except Exception as e:
             raise ServiceError(status_code=500, detail=f"Error interno al reactivar menú: {str(e)}")

    @staticmethod
    async def obtener_arbol_menu_por_area(area_id: int) -> MenuResponse:
        """Obtiene la estructura jerárquica de menús para un área específica."""
        logger.info(f"Obteniendo árbol de menú para area_id: {area_id} desde el servicio.")
        try:
            # Ejecuta la query para obtener la lista plana de menús del área
            params = (area_id,)
            menu_items_raw_list = execute_query(GET_MENUS_BY_AREA_FOR_TREE_QUERY, params)

            if not menu_items_raw_list:
                logger.info(f"No se encontraron menús para el área ID: {area_id}.")
                # Devuelve una respuesta vacía en lugar de error si no hay menús
                return MenuResponse(menu=[])

            # execute_query ya devuelve lista de dicts
            # menu_items_dict_list = [dict(row) for row in menu_items_raw_list]

            # Usa el helper para construir el árbol
            menu_tree = build_menu_tree(menu_items_raw_list) # O usa menu_items_dict_list si convertiste

            return MenuResponse(menu=menu_tree)

        except DatabaseError as db_err:
             logger.error(f"Error de DB al obtener árbol de menú para área {area_id}: {db_err}", exc_info=True)
             raise ServiceError(status_code=500, detail=f"Error DB al obtener menú del área: {getattr(db_err, 'detail', str(db_err))}")
        except Exception as e:
            logger.error(f"Error inesperado al obtener/construir árbol de menú para área {area_id}: {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="Error interno al procesar el menú del área.")