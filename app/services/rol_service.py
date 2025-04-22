# app/services/rol_service.py

from typing import Dict, List, Optional
from app.db.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import ServiceError, ValidationError
import logging

logger = logging.getLogger(__name__)

class RolService:
    @staticmethod
    async def _verificar_rol_existente(nombre: str, rol_id_excluir: Optional[int] = None) -> None:
        """
        Verifica si ya existe un rol con el mismo nombre, opcionalmente excluyendo un ID.
        Lanza ValidationError si existe.
        """
        try:
            query = "SELECT rol_id FROM rol WHERE nombre = ?"
            params = [nombre]
            if rol_id_excluir is not None:
                query += " AND rol_id != ?"
                params.append(rol_id_excluir)

            resultados = execute_query(query, tuple(params))

            if resultados:
                raise ValidationError(
                    status_code=400,
                    detail=f"El nombre de rol '{nombre}' ya está en uso."
                )
        except ValidationError as e:
            raise e # Re-lanzar para que sea capturada por el método llamador
        except Exception as e:
            logger.error(f"Error verificando rol existente ('{nombre}'): {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error en la verificación del rol: {str(e)}")

    @staticmethod
    async def crear_rol(rol_data: Dict) -> Dict:
        """
        Crea un nuevo rol en la base de datos.
        """
        try:
            nombre_rol = rol_data['nombre']
            # Verificar si el nombre ya existe
            await RolService._verificar_rol_existente(nombre_rol)

            insert_query = """
            INSERT INTO rol (nombre, descripcion, es_activo)
            OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion,
                   INSERTED.es_activo, INSERTED.fecha_creacion
            VALUES (?, ?, ?)
            """
            params = (
                nombre_rol,
                rol_data.get('descripcion'),
                rol_data.get('es_activo', True) # Valor por defecto si no se proporciona
            )

            result = execute_insert(insert_query, params)

            if not result:
                raise ServiceError(status_code=500, detail="Error creando el rol")

            logger.info(f"Rol '{result['nombre']}' (ID: {result['rol_id']}) creado exitosamente.")
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al crear rol '{rol_data.get('nombre')}': {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Error inesperado creando rol '{rol_data.get('nombre')}': {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error creando el rol: {str(e)}")

    @staticmethod
    async def obtener_rol_por_id(rol_id: int) -> Optional[Dict]:
        """
        Obtiene un rol por su ID.
        """
        try:
            query = """
            SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion
            FROM rol
            WHERE rol_id = ?
            """
            resultados = execute_query(query, (rol_id,))

            if not resultados:
                logger.debug(f"Rol con ID {rol_id} no encontrado.")
                return None

            return resultados[0] # execute_query devuelve una lista

        except Exception as e:
            logger.error(f"Error obteniendo rol por ID {rol_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo rol: {str(e)}")

    @staticmethod
    async def obtener_rol_por_nombre(nombre: str) -> Optional[Dict]:
        """
        Obtiene un rol por su nombre.
        """
        try:
            query = """
            SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion
            FROM rol
            WHERE nombre = ?
            """
            resultados = execute_query(query, (nombre,))

            if not resultados:
                logger.debug(f"Rol con nombre '{nombre}' no encontrado.")
                return None

            return resultados[0]

        except Exception as e:
            logger.error(f"Error obteniendo rol por nombre '{nombre}': {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo rol: {str(e)}")

    @staticmethod
    async def obtener_roles(skip: int = 0, limit: int = 100, activos_only: bool = False) -> List[Dict]:
        """
        Obtiene una lista de roles con paginación y filtro opcional de activos.
        """
        try:
            base_query = "SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion FROM rol"
            params = []

            if activos_only:
                base_query += " WHERE es_activo = 1"

            # Asegurar que el orden sea consistente para la paginación
            base_query += " ORDER BY rol_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([skip, limit])

            resultados = execute_query(base_query, tuple(params))
            logger.debug(f"Obtenidos {len(resultados)} roles (skip={skip}, limit={limit}, activos_only={activos_only}).")
            return resultados

        except Exception as e:
            logger.error(f"Error obteniendo lista de roles: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo roles: {str(e)}")

    @staticmethod
    async def actualizar_rol(rol_id: int, rol_data: Dict) -> Dict:
        """
        Actualiza un rol existente.
        """
        try:
            # 1. Verificar si el rol existe
            rol_actual = await RolService.obtener_rol_por_id(rol_id)
            if not rol_actual:
                raise ValidationError(status_code=404, detail=f"Rol con ID {rol_id} no encontrado.")

            # 2. Verificar duplicados si se cambia el nombre
            nuevo_nombre = rol_data.get('nombre')
            if nuevo_nombre and nuevo_nombre != rol_actual['nombre']:
                await RolService._verificar_rol_existente(nuevo_nombre, rol_id_excluir=rol_id)

            # 3. Construir la consulta de actualización dinámica
            update_parts = []
            params = []
            allowed_fields = {'nombre': 'nombre', 'descripcion': 'descripcion', 'es_activo': 'es_activo'}

            for field, db_field in allowed_fields.items():
                if field in rol_data and rol_data[field] is not None:
                    # Solo añadir si el valor es diferente al actual para evitar updates innecesarios (opcional)
                    # if rol_data[field] != rol_actual.get(field):
                    update_parts.append(f"{db_field} = ?")
                    params.append(rol_data[field])

            if not update_parts:
                # Si no hay nada que actualizar, podríamos devolver el rol actual o un mensaje
                # O lanzar un error si se espera que siempre haya algo que actualizar
                logger.info(f"No se proporcionaron campos válidos para actualizar el rol ID {rol_id}.")
                # raise ValidationError(status_code=400, detail="No hay campos válidos para actualizar")
                return rol_actual # Devolver el rol sin cambios

            # Añadir el ID del rol al final de los parámetros para el WHERE
            params.append(rol_id)

            update_query = f"""
            UPDATE rol
            SET {', '.join(update_parts)}
            OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion,
                   INSERTED.es_activo, INSERTED.fecha_creacion
            WHERE rol_id = ?
            """

            result = execute_update(update_query, tuple(params))

            if not result:
                # Esto podría ocurrir si el rol fue eliminado justo antes del update
                raise ServiceError(status_code=500, detail="Error al actualizar el rol, posible concurrencia.")

            logger.info(f"Rol '{result['nombre']}' (ID: {result['rol_id']}) actualizado exitosamente.")
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al actualizar rol ID {rol_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Error inesperado actualizando rol ID {rol_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error actualizando el rol: {str(e)}")

    @staticmethod
    async def desactivar_rol(rol_id: int) -> Dict:
        """
        Desactiva un rol (borrado lógico).
        """
        try:
            # 1. Verificar si el rol existe y está activo
            rol_actual = await RolService.obtener_rol_por_id(rol_id)
            if not rol_actual:
                raise ValidationError(status_code=404, detail=f"Rol con ID {rol_id} no encontrado.")
            if not rol_actual['es_activo']:
                logger.info(f"Rol ID {rol_id} ya se encontraba inactivo.")
                # Devolver el rol actual indicando que ya estaba inactivo
                return rol_actual

            # 2. Actualizar es_activo a False
            update_query = """
            UPDATE rol
            SET es_activo = 0
            OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion,
                   INSERTED.es_activo, INSERTED.fecha_creacion
            WHERE rol_id = ? AND es_activo = 1 -- Doble check por concurrencia
            """
            result = execute_update(update_query, (rol_id,))

            if not result:
                # Podría ser por concurrencia (alguien lo desactivó entre el check y el update)
                logger.warning(f"No se pudo desactivar el rol ID {rol_id}, posible concurrencia o ya estaba inactivo.")
                # Re-obtener el estado actual para devolverlo
                rol_actualizado = await RolService.obtener_rol_por_id(rol_id)
                if rol_actualizado and not rol_actualizado['es_activo']:
                    return rol_actualizado
                raise ServiceError(status_code=500, detail="Error al desactivar el rol, posible concurrencia.")

            logger.info(f"Rol '{result['nombre']}' (ID: {result['rol_id']}) desactivado exitosamente.")
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al desactivar rol ID {rol_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Error inesperado desactivando rol ID {rol_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error desactivando el rol: {str(e)}")