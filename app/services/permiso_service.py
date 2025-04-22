# app/services/permiso_service.py

from typing import Dict, List, Optional
from app.db.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import ServiceError, ValidationError
import logging

# Importar otros servicios si necesitamos validar IDs
from app.services.rol_service import RolService
from app.services.menu_service import MenuService # Asumiendo que tienes un MenuService

logger = logging.getLogger(__name__)

class PermisoService:

    @staticmethod
    async def _validar_rol_y_menu(rol_id: int, menu_id: int):
        """Método auxiliar para validar la existencia de rol y menú."""
        rol = await RolService.obtener_rol_por_id(rol_id)
        if not rol:
            raise ValidationError(status_code=404, detail=f"Rol con ID {rol_id} no encontrado.")
        # Asumiendo que tienes MenuService.obtener_menu_por_id
        menu = await MenuService.obtener_menu_por_id(menu_id) # Reemplaza con tu método real
        if not menu:
            raise ValidationError(status_code=404, detail=f"Menú con ID {menu_id} no encontrado.")
        # Podrías añadir validaciones de si están activos si es necesario

    @staticmethod
    async def asignar_o_actualizar_permiso(
        rol_id: int,
        menu_id: int,
        puede_ver: Optional[bool] = None,
        puede_editar: Optional[bool] = None,
        puede_eliminar: Optional[bool] = None
    ) -> Dict:
        """
        Asigna o actualiza los permisos de un rol sobre un menú.
        Si la asignación no existe, la crea. Si existe, la actualiza.
        """
        try:
            # 1. Validar Rol y Menú
            await PermisoService._validar_rol_y_menu(rol_id, menu_id)

            # 2. Verificar si ya existe un permiso para este rol y menú
            check_query = """
            SELECT rol_menu_id, puede_ver, puede_editar, puede_eliminar
            FROM rol_menu_permiso
            WHERE rol_id = ? AND menu_id = ?
            """
            existing_perm = execute_query(check_query, (rol_id, menu_id))

            permiso_data = {}
            if puede_ver is not None: permiso_data['puede_ver'] = puede_ver
            if puede_editar is not None: permiso_data['puede_editar'] = puede_editar
            if puede_eliminar is not None: permiso_data['puede_eliminar'] = puede_eliminar

            if not permiso_data:
                 raise ValidationError(status_code=400, detail="Debe proporcionar al menos un permiso (ver, editar, eliminar).")


            if existing_perm:
                # --- Actualizar Permiso Existente ---
                perm_id = existing_perm[0]['rol_menu_id']
                current_perms = existing_perm[0]
                logger.info(f"Actualizando permiso existente ID {perm_id} para Rol {rol_id}, Menú {menu_id}.")

                update_parts = []
                params = []
                # Construir SET dinámicamente solo con los valores proporcionados
                for key, value in permiso_data.items():
                    # Opcional: actualizar solo si el valor es diferente
                    # if value != current_perms.get(key):
                    update_parts.append(f"{key} = ?")
                    params.append(value)

                if not update_parts:
                    logger.info(f"No hay cambios en los permisos para ID {perm_id}.")
                    # Devolver el permiso existente sin cambios (necesitamos query completa)
                    get_query = """
                    SELECT rol_menu_id, rol_id, menu_id, puede_ver, puede_editar, puede_eliminar
                    FROM rol_menu_permiso WHERE rol_menu_id = ?
                    """
                    return execute_query(get_query, (perm_id,))[0]


                params.append(perm_id) # Añadir ID para el WHERE

                update_query = f"""
                UPDATE rol_menu_permiso
                SET {', '.join(update_parts)}
                OUTPUT INSERTED.rol_menu_id, INSERTED.rol_id, INSERTED.menu_id,
                       INSERTED.puede_ver, INSERTED.puede_editar, INSERTED.puede_eliminar
                WHERE rol_menu_id = ?
                """
                result = execute_update(update_query, tuple(params))
                if not result:
                     raise ServiceError(status_code=500, detail="Error al actualizar el permiso.")
                logger.info(f"Permiso ID {perm_id} actualizado exitosamente.")
                return result

            else:
                # --- Crear Nuevo Permiso ---
                logger.info(f"Creando nuevo permiso para Rol {rol_id}, Menú {menu_id}.")
                # Establecer valores por defecto si no se proporcionan explícitamente
                final_puede_ver = permiso_data.get('puede_ver', False) # Default a False si no se especifica al crear
                final_puede_editar = permiso_data.get('puede_editar', False)
                final_puede_eliminar = permiso_data.get('puede_eliminar', False)

                insert_query = """
                INSERT INTO rol_menu_permiso (rol_id, menu_id, puede_ver, puede_editar, puede_eliminar)
                OUTPUT INSERTED.rol_menu_id, INSERTED.rol_id, INSERTED.menu_id,
                       INSERTED.puede_ver, INSERTED.puede_editar, INSERTED.puede_eliminar
                VALUES (?, ?, ?, ?, ?)
                """
                params = (rol_id, menu_id, final_puede_ver, final_puede_editar, final_puede_eliminar)
                result = execute_insert(insert_query, params)
                if not result:
                    raise ServiceError(status_code=500, detail="Error al crear el permiso.")
                logger.info(f"Permiso creado exitosamente con ID {result['rol_menu_id']}.")
                return result

        except ValidationError as e:
            logger.warning(f"Error de validación gestionando permiso para Rol {rol_id}, Menú {menu_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Error inesperado gestionando permiso para Rol {rol_id}, Menú {menu_id}: {str(e)}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error al gestionar permiso: {str(e)}")

    @staticmethod
    async def obtener_permisos_por_rol(rol_id: int) -> List[Dict]:
        """
        Obtiene todos los permisos asignados a un rol específico.
        Incluye detalles del menú asociado.
        """
        try:
            # Validar que el rol existe
            rol = await RolService.obtener_rol_por_id(rol_id)
            if not rol:
                # Devolver lista vacía o lanzar error? Devolver lista vacía es más seguro.
                logger.warning(f"Intento de obtener permisos para rol inexistente ID {rol_id}.")
                return []

            query = """
            SELECT
                p.rol_menu_id, p.rol_id, p.menu_id,
                p.puede_ver, p.puede_editar, p.puede_eliminar,
                m.nombre AS menu_nombre, m.url AS menu_url, m.icono AS menu_icono -- Añadir campos del menú
            FROM rol_menu_permiso p
            INNER JOIN menu m ON p.menu_id = m.menu_id -- Unir con tabla menu
            WHERE p.rol_id = ?
            ORDER BY m.orden; -- Opcional: ordenar por menú
            """
            permisos = execute_query(query, (rol_id,))
            logger.debug(f"Obtenidos {len(permisos)} permisos para rol ID {rol_id}.")
            return permisos

        except Exception as e:
            logger.error(f"Error obteniendo permisos para rol ID {rol_id}: {str(e)}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error obteniendo permisos del rol: {str(e)}")

    @staticmethod
    async def obtener_permiso_especifico(rol_id: int, menu_id: int) -> Optional[Dict]:
        """
        Obtiene el permiso específico de un rol sobre un menú.
        """
        try:
            query = """
            SELECT rol_menu_id, rol_id, menu_id, puede_ver, puede_editar, puede_eliminar
            FROM rol_menu_permiso
            WHERE rol_id = ? AND menu_id = ?
            """
            resultados = execute_query(query, (rol_id, menu_id))
            if not resultados:
                logger.debug(f"No se encontró permiso para Rol {rol_id}, Menú {menu_id}.")
                return None
            return resultados[0]
        except Exception as e:
            logger.error(f"Error obteniendo permiso específico para Rol {rol_id}, Menú {menu_id}: {str(e)}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error obteniendo permiso específico: {str(e)}")


    @staticmethod
    async def revocar_permiso(rol_id: int, menu_id: int) -> Dict:
        """
        Elimina la entrada de permiso para un rol y menú específicos.
        """
        try:
            # 1. Validar Rol y Menú (opcional, pero bueno para mensajes de error claros)
            # await PermisoService._validar_rol_y_menu(rol_id, menu_id)

            # 2. Verificar si el permiso existe antes de intentar eliminar
            permiso_existente = await PermisoService.obtener_permiso_especifico(rol_id, menu_id)
            if not permiso_existente:
                 raise ValidationError(status_code=404, detail=f"No se encontró permiso para eliminar (Rol ID: {rol_id}, Menú ID: {menu_id}).")

            # 3. Ejecutar DELETE
            # Usamos execute_update porque DELETE no devuelve filas por defecto en pyodbc
            # Podríamos usar OUTPUT DELETED.* si quisiéramos los datos eliminados
            delete_query = """
            DELETE FROM rol_menu_permiso
            WHERE rol_id = ? AND menu_id = ?
            """
            # execute_update maneja commit/rollback pero no devuelve datos en DELETE simple
            # Para confirmar, podemos verificar las filas afectadas si la librería lo permite
            # o simplemente asumir éxito si no hay excepción.
            # Por simplicidad, usaremos execute_query para simular un DELETE que no necesita retorno
            with execute_query(delete_query, (rol_id, menu_id)) as cursor:
                 pass # La ejecución ocurre dentro del context manager de execute_query/update/insert

            logger.info(f"Permiso revocado exitosamente para Rol {rol_id}, Menú {menu_id}.")
            return {"message": "Permiso revocado exitosamente"}

        except ValidationError as e:
            logger.warning(f"Error de validación revocando permiso para Rol {rol_id}, Menú {menu_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Error inesperado revocando permiso para Rol {rol_id}, Menú {menu_id}: {str(e)}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"Error al revocar permiso: {str(e)}")

    # Podrías añadir métodos para revocar todos los permisos de un rol o menú si es necesario
    # async def revocar_todos_permisos_por_rol(rol_id: int): ...
    # async def revocar_todos_permisos_por_menu(menu_id: int): ...