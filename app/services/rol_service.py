# app/services/rol_service.py
from fastapi import status
import math
from typing import Dict, List, Optional
# Importar las queries necesarias, incluyendo REACTIVATE_ROL
from app.db.queries import (
    execute_query, execute_insert, execute_update, execute_transaction,
    COUNT_ROLES_PAGINATED, SELECT_ROLES_PAGINATED,
    DEACTIVATE_ROL, REACTIVATE_ROL, # <-- Añadir DEACTIVATE_ROL y REACTIVATE_ROL
    SELECT_PERMISOS_POR_ROL,
    DELETE_PERMISOS_POR_ROL,
    INSERT_PERMISO_ROL
)
from app.schemas.rol import (    
    # --- AÑADIR IMPORTACIONES DE SCHEMAS DE PERMISOS ---
    PermisoRead, PermisoUpdatePayload, PermisoBase
)
from app.core.exceptions import ServiceError, ValidationError, DatabaseError
import logging
import pyodbc

logger = logging.getLogger(__name__)

class RolService:
    # --- Métodos existentes (_verificar_rol_existente, crear_rol, etc.) ---
    # ... (código existente sin cambios) ...
    @staticmethod
    async def _verificar_rol_existente(nombre: str, rol_id_excluir: Optional[int] = None) -> None:
        """
        Verifica si ya existe un rol con el mismo nombre, opcionalmente excluyendo un ID.
        Lanza ValidationError si existe.
        """
        try:
            # Usar LOWER para comparación insensible a mayúsculas/minúsculas
            query = "SELECT rol_id FROM rol WHERE LOWER(nombre) = LOWER(?)"
            params = [nombre]
            if rol_id_excluir is not None:
                query += " AND rol_id != ?"
                params.append(rol_id_excluir)

            resultados = execute_query(query, tuple(params)) # No necesita await si execute_query es síncrona

            if resultados:
                raise ValidationError(
                    status_code=409, # Usar 409 Conflict para duplicados
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
            nombre_rol = rol_data.get('nombre')
            if not nombre_rol: # Validar que el nombre no sea None o vacío
                 raise ValidationError(status_code=400, detail="El nombre del rol es requerido.")

            # Verificar si el nombre ya existe
            await RolService._verificar_rol_existente(nombre_rol) # Usar await si _verificar_rol_existente es async

            # Usar la query definida en queries.py si existe, o mantenerla aquí
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

            result = execute_insert(insert_query, params) # No necesita await si execute_insert es síncrona

            if not result: # execute_insert devuelve {} si no hay OUTPUT o falla silenciosamente
                # Podría ser mejor que execute_insert lance error si falla
                raise ServiceError(status_code=500, detail="La creación del rol no devolvió resultados.")

            logger.info(f"Rol '{result.get('nombre', 'N/A')}' (ID: {result.get('rol_id', 'N/A')}) creado exitosamente.")
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al crear rol '{rol_data.get('nombre')}': {e.detail}")
            raise e
        except ServiceError as e: # Capturar ServiceError si execute_insert lo lanza
             logger.error(f"Error de servicio al crear rol '{rol_data.get('nombre')}': {e.detail}")
             raise e
        except Exception as e:
            logger.exception(f"Error inesperado creando rol '{rol_data.get('nombre')}': {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error inesperado creando el rol: {str(e)}")

    @staticmethod
    async def obtener_rol_por_id(rol_id: int, incluir_inactivos: bool = False) -> Optional[Dict]:
        """
        Obtiene un rol por su ID.
        Permite opcionalmente incluir roles inactivos.
        """
        try:
            # Modificar query para incluir inactivos si se solicita
            query = """
            SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion
            FROM rol
            WHERE rol_id = ?
            """
            params = [rol_id]
            if not incluir_inactivos:
                query += " AND es_activo = 1" # Por defecto solo activos

            resultados = execute_query(query, tuple(params)) # No necesita await

            if not resultados:
                logger.debug(f"Rol con ID {rol_id} no encontrado (incluir_inactivos={incluir_inactivos}).")
                return None

            # Convertir es_activo a bool si es necesario
            rol = resultados[0]
            if 'es_activo' in rol and isinstance(rol['es_activo'], int):
                 rol['es_activo'] = bool(rol['es_activo'])
            return rol

        except Exception as e:
            logger.exception(f"Error obteniendo rol por ID {rol_id}: {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error obteniendo rol: {str(e)}")

    @staticmethod
    async def obtener_rol_por_nombre(nombre: str, incluir_inactivos: bool = False) -> Optional[Dict]:
        """
        Obtiene un rol por su nombre.
        Permite opcionalmente incluir roles inactivos.
        """
        try:
            # Modificar query para incluir inactivos si se solicita
            query = """
            SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion
            FROM rol
            WHERE LOWER(nombre) = LOWER(?) -- Comparación insensible
            """
            params = [nombre]
            if not incluir_inactivos:
                query += " AND es_activo = 1" # Por defecto solo activos

            resultados = execute_query(query, tuple(params)) # No necesita await

            if not resultados:
                logger.debug(f"Rol con nombre '{nombre}' no encontrado (incluir_inactivos={incluir_inactivos}).")
                return None

            # Convertir es_activo a bool si es necesario
            rol = resultados[0]
            if 'es_activo' in rol and isinstance(rol['es_activo'], int):
                 rol['es_activo'] = bool(rol['es_activo'])
            return rol

        except Exception as e:
            logger.exception(f"Error obteniendo rol por nombre '{nombre}': {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error obteniendo rol: {str(e)}")

    @staticmethod
    async def obtener_roles(skip: int = 0, limit: int = 100, activos_only: bool = False) -> List[Dict]:
        """
        Obtiene una lista de roles con paginación simple (OFFSET/FETCH) y filtro opcional de activos.
        NOTA: Este método no devuelve el conteo total y no soporta búsqueda. Usar obtener_roles_paginados para eso.
        """
        try:
            base_query = "SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion FROM rol"
            params = []

            if activos_only:
                base_query += " WHERE es_activo = 1"

            # Asegurar que el orden sea consistente para la paginación
            base_query += " ORDER BY rol_id OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([skip, limit])

            resultados = execute_query(base_query, tuple(params)) # No necesita await
            logger.debug(f"Obtenidos {len(resultados)} roles (skip={skip}, limit={limit}, activos_only={activos_only}).")

            # Convertir es_activo a bool si es necesario
            roles_procesados = []
            for rol_dict in resultados:
                 if 'es_activo' in rol_dict and isinstance(rol_dict['es_activo'], int):
                      rol_dict['es_activo'] = bool(rol_dict['es_activo'])
                 roles_procesados.append(rol_dict)
            return roles_procesados

        except Exception as e:
            logger.exception(f"Error obteniendo lista de roles: {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error obteniendo roles: {str(e)}")

    @staticmethod
    async def actualizar_rol(rol_id: int, rol_data: Dict) -> Dict:
        """
        Actualiza un rol existente.
        """
        try:
            # 1. Verificar si el rol existe (incluyendo inactivos para poder actualizarlo)
            rol_actual = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True) # Usar await
            if not rol_actual:
                raise ValidationError(status_code=404, detail=f"Rol con ID {rol_id} no encontrado.")

            # 2. Verificar duplicados si se cambia el nombre
            nuevo_nombre = rol_data.get('nombre')
            if nuevo_nombre and nuevo_nombre != rol_actual.get('nombre'):
                await RolService._verificar_rol_existente(nuevo_nombre, rol_id_excluir=rol_id) # Usar await

            # 3. Construir la consulta de actualización dinámica (tu lógica original)
            update_parts = []
            params = []
            allowed_fields = {'nombre': 'nombre', 'descripcion': 'descripcion', 'es_activo': 'es_activo'}

            campos_a_actualizar = False
            for field, db_field in allowed_fields.items():
                # Verificar si el campo está en rol_data y es diferente al valor actual
                # Permitir actualizar 'es_activo' incluso si es el mismo valor (para simplificar)
                if field in rol_data and rol_data[field] is not None:
                    # Comparar solo si no es 'es_activo' o si es diferente
                    if field != 'es_activo' or rol_data[field] != rol_actual.get(field):
                        update_parts.append(f"{db_field} = ?")
                        params.append(rol_data[field])
                        campos_a_actualizar = True

            if not campos_a_actualizar:
                logger.info(f"No se detectaron cambios para actualizar el rol ID {rol_id}.")
                return rol_actual # Devolver el rol sin cambios si no hay nada que actualizar

            # Añadir fecha_actualizacion si existe en la tabla
            # update_parts.append("fecha_actualizacion = GETDATE()") # Asumiendo SQL Server

            # Añadir el ID del rol al final de los parámetros para el WHERE
            params.append(rol_id)

            # Usar la query UPDATE_ROL de queries.py si es adecuada, o mantener la dinámica
            # Si se usa UPDATE_ROL, asegurarse que los parámetros coincidan
            update_query = f"""
            UPDATE rol
            SET {', '.join(update_parts)}
            OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion,
                   INSERTED.es_activo, INSERTED.fecha_creacion -- Añadir fecha_actualizacion si se quiere devolver
            WHERE rol_id = ?
            """

            result = execute_update(update_query, tuple(params)) # No necesita await

            if not result:
                # Esto podría ocurrir si el rol fue eliminado justo antes del update
                # O si execute_update devuelve {} en lugar de lanzar error
                logger.error(f"La actualización del rol ID {rol_id} no devolvió resultados.")
                raise ServiceError(status_code=500, detail="Error al actualizar el rol, posible concurrencia o fallo en la BD.")

            logger.info(f"Rol '{result.get('nombre', 'N/A')}' (ID: {result.get('rol_id', 'N/A')}) actualizado exitosamente.")
            # Convertir es_activo a bool si es necesario
            if 'es_activo' in result and isinstance(result['es_activo'], int):
                 result['es_activo'] = bool(result['es_activo'])
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al actualizar rol ID {rol_id}: {e.detail}")
            raise e
        except ServiceError as e: # Capturar ServiceError si execute_update lo lanza
             logger.error(f"Error de servicio al actualizar rol ID {rol_id}: {e.detail}")
             raise e
        except Exception as e:
            logger.exception(f"Error inesperado actualizando rol ID {rol_id}: {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error inesperado actualizando el rol: {str(e)}")

    @staticmethod
    async def desactivar_rol(rol_id: int) -> Dict:
        """
        Desactiva un rol (borrado lógico).
        """
        try:
            # 1. Verificar si el rol existe y está activo
            # Usamos incluir_inactivos=True para dar un mensaje más específico si ya está inactivo
            rol_actual = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True) # Usar await
            if not rol_actual:
                raise ValidationError(status_code=404, detail=f"Rol con ID {rol_id} no encontrado.")
            if not rol_actual.get('es_activo', False): # Si no está activo
                logger.info(f"Rol ID {rol_id} ya se encontraba inactivo.")
                # Devolver el rol actual indicando que ya estaba inactivo
                # Podríamos lanzar un error 400 Bad Request si se prefiere
                # raise ValidationError(status_code=400, detail=f"Rol con ID {rol_id} ya está inactivo.")
                return rol_actual

            # 2. Usar la query DEACTIVATE_ROL de queries.py
            result = execute_update(DEACTIVATE_ROL, (rol_id,)) # No necesita await

            if not result:
                # Podría ser por concurrencia (alguien lo desactivó entre el check y el update)
                # O si la query DEACTIVATE_ROL no encontró la fila (ya estaba inactivo o no existe)
                logger.warning(f"No se pudo desactivar el rol ID {rol_id}, posible concurrencia o ya estaba inactivo.")
                # Re-obtener el estado actual para devolverlo o lanzar error
                rol_revisado = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True) # Usar await
                if rol_revisado and not rol_revisado.get('es_activo'):
                    return rol_revisado # Devolver el estado inactivo confirmado
                # Si sigue activo o no se encuentra, lanzar error
                raise ServiceError(status_code=500, detail="Error al desactivar el rol, estado inconsistente o rol no encontrado.")

            logger.info(f"Rol '{result.get('nombre', 'N/A')}' (ID: {result.get('rol_id', 'N/A')}) desactivado exitosamente.")
            # Convertir es_activo a bool si es necesario
            if 'es_activo' in result and isinstance(result['es_activo'], int):
                 result['es_activo'] = bool(result['es_activo'])
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al desactivar rol ID {rol_id}: {e.detail}")
            raise e
        except ServiceError as e: # Capturar ServiceError si execute_update lo lanza
             logger.error(f"Error de servicio al desactivar rol ID {rol_id}: {e.detail}")
             raise e
        except Exception as e:
            logger.exception(f"Error inesperado desactivando rol ID {rol_id}: {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error inesperado desactivando el rol: {str(e)}")

    # --- NUEVO MÉTODO PARA REACTIVAR ROL ---
    @staticmethod
    async def reactivar_rol(rol_id: int) -> Dict:
        """
        Reactiva un rol que estaba inactivo (borrado lógico).
        """
        try:
            # 1. Verificar si el rol existe y está INACTIVO
            # Usamos incluir_inactivos=True para encontrarlo si está inactivo
            rol_actual = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True) # Usar await
            if not rol_actual:
                raise ValidationError(status_code=404, detail=f"Rol con ID {rol_id} no encontrado.")
            if rol_actual.get('es_activo', False): # Si ya está activo
                logger.info(f"Rol ID {rol_id} ya se encontraba activo.")
                # Devolver el rol actual indicando que ya estaba activo
                # O lanzar un error 400 Bad Request
                # raise ValidationError(status_code=400, detail=f"Rol con ID {rol_id} ya está activo.")
                return rol_actual

            # 2. Usar la query REACTIVATE_ROL de queries.py
            result = execute_update(REACTIVATE_ROL, (rol_id,)) # No necesita await

            if not result:
                # Podría ser por concurrencia (alguien lo reactivó o eliminó entre el check y el update)
                # O si la query REACTIVATE_ROL no encontró la fila (ya estaba activo o no existe)
                logger.warning(f"No se pudo reactivar el rol ID {rol_id}, posible concurrencia o ya estaba activo.")
                # Re-obtener el estado actual para devolverlo o lanzar error
                rol_revisado = await RolService.obtener_rol_por_id(rol_id, incluir_inactivos=True) # Usar await
                if rol_revisado and rol_revisado.get('es_activo'):
                    return rol_revisado # Devolver el estado activo confirmado
                # Si sigue inactivo o no se encuentra, lanzar error
                raise ServiceError(status_code=500, detail="Error al reactivar el rol, estado inconsistente o rol no encontrado.")

            logger.info(f"Rol '{result.get('nombre', 'N/A')}' (ID: {result.get('rol_id', 'N/A')}) reactivado exitosamente.")
            # Convertir es_activo a bool si es necesario (aunque debería ser True)
            if 'es_activo' in result and isinstance(result['es_activo'], int):
                 result['es_activo'] = bool(result['es_activo'])
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al reactivar rol ID {rol_id}: {e.detail}")
            raise e
        except ServiceError as e: # Capturar ServiceError si execute_update lo lanza
             logger.error(f"Error de servicio al reactivar rol ID {rol_id}: {e.detail}")
             raise e
        except Exception as e:
            logger.exception(f"Error inesperado reactivando rol ID {rol_id}: {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error inesperado reactivando el rol: {str(e)}")
    # --- FIN NUEVO MÉTODO ---


    # --- MÉTODO PARA LISTADO PAGINADO (Existente - SIN CAMBIOS) ---
    @staticmethod
    async def obtener_roles_paginados( # Nombre en español mantenido
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Dict:
        """
        Obtiene una lista paginada de roles (activos e inactivos).
        Permite búsqueda por nombre o descripción (insensible a mayúsculas/minúsculas).
        """
        logger.info(f"Iniciando obtener_roles_paginados: page={page}, limit={limit}, search='{search}'")

        # Validar entrada
        if page < 1:
            raise ValidationError(status_code=400, detail="El número de página debe ser mayor o igual a 1.")
        if limit < 1:
            # Permitir limit=0 podría tener sentido si solo se quiere el conteo, pero usualmente no.
            raise ValidationError(status_code=400, detail="El límite por página debe ser mayor o igual a 0.")

        offset = (page - 1) * limit
        # Preparar parámetro de búsqueda para LIKE (insensible a mayúsculas/minúsculas ya manejado en SQL con LOWER())
        search_param = f"%{search}%" if search else None
        # Parámetros para las queries (3 para WHERE, 2 para OFFSET/FETCH)
        # El primer '?' en las queries es para el IS NULL check
        count_params = (search_param, search_param, search_param)
        select_params = (search_param, search_param, search_param, offset, limit)

        try:
            # --- 1. Contar el total de roles que coinciden ---
            logger.debug(f"Ejecutando COUNT_ROLES_PAGINATED con params: {count_params}")
            count_result = execute_query(COUNT_ROLES_PAGINATED, count_params) # No necesita await

            # Validar resultado del conteo
            if not count_result or not isinstance(count_result, list) or len(count_result) == 0 or 'total' not in count_result[0]:
                 logger.error(f"Error al contar roles: la consulta COUNT_ROLES_PAGINATED no devolvió el resultado esperado ('total'). Resultado: {count_result}")
                 raise ServiceError(status_code=500, detail="Error al obtener el total de roles.")

            total_roles = count_result[0]['total']
            logger.debug(f"Total de roles encontrados (sin paginar): {total_roles}")

            # --- 2. Obtener los datos paginados de los roles (solo si hay roles o limit > 0) ---
            lista_roles = []
            if total_roles > 0 and limit > 0:
                logger.debug(f"Ejecutando SELECT_ROLES_PAGINATED con params: {select_params}")
                lista_roles = execute_query(SELECT_ROLES_PAGINATED, select_params) # No necesita await
                logger.debug(f"Obtenidos {len(lista_roles)} roles para la página {page}.")
            elif limit == 0:
                 logger.debug("Limit es 0, no se recuperan roles, solo el conteo.")
            else:
                 logger.debug("Total de roles es 0, no se recuperan roles.")


            # --- 3. Calcular total de páginas ---
            total_paginas = math.ceil(total_roles / limit) if limit > 0 else 0

            # --- 4. Procesar y construir el diccionario de respuesta final ---
            roles_procesados = []
            for rol_dict in lista_roles:
                 # Asegurar que es_activo sea booleano
                 if 'es_activo' in rol_dict and isinstance(rol_dict['es_activo'], int):
                      rol_dict['es_activo'] = bool(rol_dict['es_activo'])
                 # Aquí podrías validar cada rol_dict contra RolRead si quieres ser muy estricto
                 roles_procesados.append(rol_dict)

            response_data = {
                "roles": roles_procesados,
                "total_roles": total_roles,
                "pagina_actual": page,
                "total_paginas": total_paginas
            }

            logger.info(f"obtener_roles_paginados completado exitosamente.")
            return response_data

        except ValidationError as ve:
             logger.warning(f"Error de validación en obtener_roles_paginados: {ve.detail}")
             raise ve # Re-lanzar error de validación
        except ServiceError as se: # Capturar errores de servicio específicos si ocurren
             logger.error(f"Error de servicio en obtener_roles_paginados: {se.detail}")
             raise se
        except Exception as e:
            logger.exception(f"Error inesperado en obtener_roles_paginados: {str(e)}") # Usar exception
            raise ServiceError(status_code=500, detail=f"Error obteniendo la lista paginada de roles: {str(e)}")

    @staticmethod
    async def get_all_active_roles() -> List[Dict]:
        """
        Obtiene una lista de todos los roles activos, ordenados por nombre.
        No utiliza paginación.

        Returns:
            Una lista de diccionarios, donde cada diccionario representa un rol activo.
            Devuelve una lista vacía si no hay roles activos o en caso de error.

        Raises:
            ServiceError: Si ocurre un error inesperado durante la consulta.
        """
        logger.debug("Iniciando get_all_active_roles.")
        query = """
            SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion
            FROM rol
            WHERE es_activo = 1
            ORDER BY nombre ASC;
        """
        try:
            # Asumiendo que execute_query maneja la conexión y es síncrona
            # (basado en el uso sin 'await' en otros métodos)
            resultados = execute_query(query)

            roles_procesados = []
            for rol_dict in resultados:
                # Asegurar que es_activo sea booleano
                if 'es_activo' in rol_dict and isinstance(rol_dict['es_activo'], int):
                    rol_dict['es_activo'] = bool(rol_dict['es_activo'])
                roles_procesados.append(rol_dict)

            logger.info(f"Se encontraron {len(roles_procesados)} roles activos.")
            return roles_procesados

        except Exception as e:
            logger.exception(f"Error inesperado obteniendo todos los roles activos: {str(e)}")
            # Lanzar ServiceError para ser manejado en el endpoint
            raise ServiceError(status_code=500, detail=f"Error obteniendo la lista de roles activos: {str(e)}")

    @staticmethod
    async def obtener_permisos_por_rol(rol_id: int) -> List[PermisoRead]:
        """
        Obtiene la lista de permisos asignados a un rol específico.

        Args:
            rol_id: El ID del rol cuyos permisos se quieren obtener.

        Returns:
            Lista de objetos PermisoRead representando los permisos asignados.

        Raises:
            ServiceError: Si el rol no existe (404) o si ocurre un error de BD (500).
        """
        logger.info(f"Obteniendo permisos para el rol ID: {rol_id}")

        # Verificar si el rol existe usando el método estático
        rol_existente = await RolService.obtener_rol_por_id(rol_id)
        if not rol_existente:
             logger.warning(f"Intento de obtener permisos para rol inexistente ID: {rol_id}")
             # --- LANZAR ServiceError EN LUGAR DE DEVOLVER [] O NotFoundError ---
             raise ServiceError(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")

        try:
            resultados = execute_query(SELECT_PERMISOS_POR_ROL, (rol_id,))
            if not resultados:
                logger.info(f"El rol ID {rol_id} no tiene permisos asignados.")
                return [] # Devolver lista vacía si no hay permisos es correcto

            permisos = [PermisoRead(**dict(row)) for row in resultados]
            logger.info(f"Se encontraron {len(permisos)} permisos para el rol ID: {rol_id}")
            return permisos

        except DatabaseError as db_error:
             logger.error(f"Error de base de datos al obtener permisos para rol {rol_id}: {db_error}", exc_info=True)
             # Lanzar ServiceError consistente
             raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de base de datos al obtener permisos: {db_error.detail}")
        except Exception as e:
            logger.exception(f"Error inesperado al obtener permisos para rol {rol_id}: {e}")
            # Lanzar ServiceError consistente
            raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al obtener permisos.")
    
    # --- NUEVO MÉTODO: ACTUALIZAR PERMISOS DE ROL ---
    @staticmethod
    async def actualizar_permisos_rol(rol_id: int, permisos_payload: PermisoUpdatePayload) -> None:
        logger.info(f"Iniciando actualización de permisos para el rol ID: {rol_id}")

        # 1. Verificar si el rol existe (fuera de la transacción)
        rol_existente = await RolService.obtener_rol_por_id(rol_id)
        if not rol_existente:
            raise ServiceError(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado para actualizar permisos.")

        nuevos_permisos: List[PermisoBase] = permisos_payload.permisos
        logger.debug(f"Se actualizarán {len(nuevos_permisos)} permisos para el rol {rol_id}.")

        # 2. Definir la función que contiene las operaciones de la transacción
        def _operaciones_permisos(cursor: pyodbc.Cursor): # La función recibe el cursor
            # Borrar permisos existentes
            logger.debug(f"Borrando permisos existentes para rol {rol_id} en transacción.")
            cursor.execute(DELETE_PERMISOS_POR_ROL, (rol_id,))
            logger.debug(f"Permisos existentes borrados para rol {rol_id}.")

            # Insertar nuevos permisos
            if nuevos_permisos:
                logger.debug(f"Insertando {len(nuevos_permisos)} nuevos permisos para rol {rol_id}.")
                insert_count = 0
                for permiso in nuevos_permisos:
                    # --- VALIDACIÓN DE DATOS (IMPORTANTE) ---
                    # Aquí es donde ocurre el IntegrityError si menu_id es inválido.
                    # El error de BD es correcto, pero el problema son los datos de entrada.
                    params = (rol_id, permiso.menu_id, permiso.puede_ver, permiso.puede_editar, permiso.puede_eliminar)
                    cursor.execute(INSERT_PERMISO_ROL, params)
                    insert_count += 1
                logger.debug(f"Insertados {insert_count} permisos para rol {rol_id}.")
            else:
                 logger.debug(f"No hay nuevos permisos para insertar para rol {rol_id}.")
            # --- NO HACER COMMIT NI ROLLBACK AQUÍ ---

        try:
            # 3. Llamar a execute_transaction pasando la función de operaciones
            execute_transaction(_operaciones_permisos)
            logger.info(f"Permisos actualizados exitosamente para el rol ID: {rol_id}")

        except DatabaseError as db_error: # Capturar DatabaseError de execute_transaction
            logger.error(f"Error de base de datos durante la transacción de permisos para rol {rol_id}: {db_error}", exc_info=True)
            # Relanzar como ServiceError
            raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de base de datos al actualizar permisos: {db_error.detail}")
        except Exception as e: # Capturar cualquier otro error inesperado
            logger.exception(f"Error inesperado durante la actualización de permisos para rol {rol_id}: {e}")
            raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar permisos.")

# --- FIN DE LA CLASE RolService ---