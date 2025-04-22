# app/services/usuario_service.py (MODIFICADO)

from datetime import datetime # <--- AÑADIR ESTA LÍNEA
import math # Necesario para calcular total_paginas
from typing import Dict, List, Optional
# Asegúrate que estas funciones manejen correctamente conexiones/cursores asíncronos si es necesario
from app.db.queries import execute_query, execute_insert, execute_update, execute_auth_query
from app.core.exceptions import ServiceError, ValidationError
from app.core.security import get_password_hash
# --- Importar y configurar logger ---
from app.core.logging_config import get_logger # Importa tu configuración de logger
# --- Importar RolService ---
# Necesario para validar roles en asignar_rol_a_usuario
from app.services.rol_service import RolService

# Asegúrate que las nuevas queries estén importadas o accesibles
from app.db.queries import (
    execute_query, execute_insert, execute_update, execute_auth_query,
    SELECT_USUARIOS_PAGINATED, # <--- NUEVA QUERY
    COUNT_USUARIOS_PAGINATED   # <--- NUEVA QUERY
)

# Necesitamos los schemas para estructurar la respuesta y para los tipos internos
from app.schemas.usuario import UsuarioReadWithRoles, PaginatedUsuarioResponse
from app.schemas.rol import RolRead

# --- Inicializar logger ---
logger = get_logger(__name__) # Usa el logger configurado

class UsuarioService:

    # --- MÉTODO NUEVO: Obtener solo nombres de roles para un usuario ---
    @staticmethod
    async def get_user_role_names(user_id: int) -> List[str]:
        """
        Obtiene la lista de NOMBRES de roles activos para un usuario dado su ID.
        Optimizado para el endpoint de login.
        """
        role_names = []
        try:
            # Query para obtener solo los nombres de los roles activos
            query = """
            SELECT r.nombre
            FROM dbo.rol r
            INNER JOIN dbo.usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = ? AND ur.es_activo = 1 AND r.es_activo = 1;
            """
            # Usar execute_query que debería devolver una lista de diccionarios
            results = execute_query(query, (user_id,)) # execute_query debe ser async si la conexión lo es

            if results:
                # Extraer el nombre de cada diccionario en la lista
                role_names = [row['nombre'] for row in results if 'nombre' in row]
                logger.debug(f"Nombres de roles obtenidos para usuario ID {user_id}: {role_names}")
            else:
                logger.debug(f"No se encontraron roles activos para usuario ID {user_id}")

        except Exception as e:
            logger.exception(f"Error en get_user_role_names para usuario ID {user_id}: {e}")
            # Re-lanzar para que el endpoint lo maneje como error 500
            raise ServiceError(status_code=500, detail=f"Error obteniendo nombres de roles: {str(e)}")

        return role_names
    # --- FIN MÉTODO NUEVO ---


    # --- MÉTODOS EXISTENTES (modificados para usar logger y async si es necesario) ---

    @staticmethod
    async def obtener_usuario_por_id(usuario_id: int) -> Optional[Dict]:
        """
        Obtiene un usuario por su ID (excluyendo eliminados).
        """
        try:
            query = """
            SELECT
                usuario_id, nombre_usuario, correo, nombre, apellido,
                es_activo, correo_confirmado, fecha_creacion, fecha_ultimo_acceso,
                fecha_actualizacion
            FROM dbo.usuario -- Añadir esquema dbo si es necesario
            WHERE usuario_id = ? AND es_eliminado = 0
            """
            # Asumiendo que execute_query devuelve lista de dicts
            resultados = execute_query(query, (usuario_id,)) # Debe ser await si execute_query es async

            if not resultados:
                logger.debug(f"Usuario con ID {usuario_id} no encontrado o está eliminado.")
                return None

            return resultados[0]

        except Exception as e:
            logger.exception(f"Error obteniendo usuario por ID {usuario_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo usuario: {str(e)}")


    @staticmethod
    async def asignar_rol_a_usuario(usuario_id: int, rol_id: int) -> Dict:
        """
        Asigna un rol a un usuario. Si la asignación existe e inactiva, la reactiva.
        """
        try:
            # 1. Validar que el usuario existe y está activo
            usuario = await UsuarioService.obtener_usuario_por_id(usuario_id)
            if not usuario:
                raise ValidationError(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado.")
            # Comentar o ajustar si permites asignar roles a usuarios inactivos
            # if not usuario['es_activo']:
            #      raise ValidationError(status_code=400, detail=f"Usuario con ID {usuario_id} no está activo.")

            # 2. Validar que el rol existe y está activo usando RolService
            rol = await RolService.obtener_rol_por_id(rol_id) # Asume que RolService tiene este método estático async
            if not rol:
                raise ValidationError(status_code=404, detail=f"Rol con ID {rol_id} no encontrado.")
            if not rol['es_activo']:
                raise ValidationError(status_code=400, detail=f"Rol con ID {rol_id} no está activo.")

            # 3. Verificar si la asignación ya existe
            check_query = """
            SELECT usuario_rol_id, es_activo
            FROM dbo.usuario_rol -- Añadir esquema dbo si es necesario
            WHERE usuario_id = ? AND rol_id = ?
            """
            existing_assignment = execute_query(check_query, (usuario_id, rol_id)) # Debe ser await si es async

            if existing_assignment:
                assignment = existing_assignment[0]
                if assignment['es_activo']:
                    logger.info(f"Rol ID {rol_id} ya está asignado y activo para usuario ID {usuario_id}.")
                    # Obtener datos completos de la asignación existente
                    get_assignment_query = """
                    SELECT usuario_rol_id, usuario_id, rol_id, fecha_asignacion, es_activo
                    FROM dbo.usuario_rol WHERE usuario_rol_id = ?
                    """
                    final_result = execute_query(get_assignment_query, (assignment['usuario_rol_id'],)) # await?
                    if not final_result:
                         raise ServiceError(status_code=500, detail="Error obteniendo datos de asignación existente.")
                    return final_result[0]
                else:
                    # Reactivar la asignación existente
                    logger.info(f"Reactivando asignación existente para usuario ID {usuario_id}, rol ID {rol_id}.")
                    update_query = """
                    UPDATE dbo.usuario_rol -- Añadir esquema dbo si es necesario
                    SET es_activo = 1, fecha_asignacion = GETDATE() -- Actualizar fecha?
                    OUTPUT INSERTED.usuario_rol_id, INSERTED.usuario_id, INSERTED.rol_id,
                           INSERTED.fecha_asignacion, INSERTED.es_activo
                    WHERE usuario_rol_id = ?
                    """
                    result = execute_update(update_query, (assignment['usuario_rol_id'],)) # await?
                    if not result:
                         raise ServiceError(status_code=500, detail="Error reactivando la asignación de rol.")
                    logger.info(f"Asignación reactivada exitosamente.")
                    return result
            else:
                # Crear nueva asignación
                logger.info(f"Creando nueva asignación para usuario ID {usuario_id}, rol ID {rol_id}.")
                insert_query = """
                INSERT INTO dbo.usuario_rol (usuario_id, rol_id, es_activo) -- Añadir esquema dbo si es necesario
                OUTPUT INSERTED.usuario_rol_id, INSERTED.usuario_id, INSERTED.rol_id,
                       INSERTED.fecha_asignacion, INSERTED.es_activo
                VALUES (?, ?, 1)
                """
                result = execute_insert(insert_query, (usuario_id, rol_id)) # await?
                if not result:
                    raise ServiceError(status_code=500, detail="Error creando la asignación de rol.")
                logger.info(f"Asignación creada exitosamente.")
                return result

        except ValidationError as e:
            logger.warning(f"Error de validación asignando rol {rol_id} a usuario {usuario_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.exception(f"Error inesperado asignando rol {rol_id} a usuario {usuario_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error asignando rol: {str(e)}")

    @staticmethod
    async def revocar_rol_de_usuario(usuario_id: int, rol_id: int) -> Dict:
        """
        Revoca (desactiva) un rol asignado a un usuario.
        """
        try:
            # 1. Verificar si la asignación existe
            check_query = """
            SELECT usuario_rol_id, es_activo
            FROM dbo.usuario_rol -- Añadir esquema dbo si es necesario
            WHERE usuario_id = ? AND rol_id = ?
            """
            existing_assignment = execute_query(check_query, (usuario_id, rol_id)) # await?

            if not existing_assignment:
                 raise ValidationError(status_code=404, detail=f"No existe asignación entre usuario ID {usuario_id} y rol ID {rol_id}.")

            assignment = existing_assignment[0]
            if not assignment['es_activo']:
                logger.info(f"La asignación entre usuario ID {usuario_id} y rol ID {rol_id} ya estaba inactiva.")
                get_assignment_query = """
                SELECT usuario_rol_id, usuario_id, rol_id, fecha_asignacion, es_activo
                FROM dbo.usuario_rol WHERE usuario_rol_id = ?
                """
                final_result = execute_query(get_assignment_query, (assignment['usuario_rol_id'],)) # await?
                return final_result[0] if final_result else {"message": "Asignación ya inactiva"}

            # 2. Desactivar la asignación
            logger.info(f"Desactivando asignación para usuario ID {usuario_id}, rol ID {rol_id}.")
            update_query = """
            UPDATE dbo.usuario_rol -- Añadir esquema dbo si es necesario
            SET es_activo = 0
            OUTPUT INSERTED.usuario_rol_id, INSERTED.usuario_id, INSERTED.rol_id,
                   INSERTED.fecha_asignacion, INSERTED.es_activo
            WHERE usuario_rol_id = ? AND es_activo = 1
            """
            result = execute_update(update_query, (assignment['usuario_rol_id'],)) # await?

            if not result:
                logger.warning(f"No se pudo desactivar la asignación ID {assignment['usuario_rol_id']}, posible concurrencia o ya estaba inactiva.")
                # Devolver el estado actual si no se pudo actualizar
                get_assignment_query = """
                SELECT usuario_rol_id, usuario_id, rol_id, fecha_asignacion, es_activo
                FROM dbo.usuario_rol WHERE usuario_rol_id = ?
                """
                final_result = execute_query(get_assignment_query, (assignment['usuario_rol_id'],)) # await?
                return final_result[0] if final_result else {"message": "No se pudo desactivar la asignación"}


            logger.info(f"Asignación desactivada exitosamente.")
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación revocando rol {rol_id} de usuario {usuario_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.exception(f"Error inesperado revocando rol {rol_id} de usuario {usuario_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error revocando rol: {str(e)}")

    @staticmethod
    async def obtener_roles_de_usuario(usuario_id: int) -> List[Dict]:
        """
        Obtiene la lista de diccionarios de roles activos asignados a un usuario.
        """
        try:
            # Validar que el usuario existe (opcional pero recomendado)
            # usuario = await UsuarioService.obtener_usuario_por_id(usuario_id)
            # if not usuario:
            #     logger.warning(f"Intento de obtener roles para usuario inexistente ID {usuario_id}.")
            #     return []

            query = """
            SELECT
                r.rol_id, r.nombre, r.descripcion, r.es_activo, r.fecha_creacion
            FROM dbo.rol r -- Añadir esquema dbo si es necesario
            INNER JOIN dbo.usuario_rol ur ON r.rol_id = ur.rol_id -- Añadir esquema dbo si es necesario
            WHERE ur.usuario_id = ? AND ur.es_activo = 1 AND r.es_activo = 1
            ORDER BY r.nombre;
            """
            roles = execute_query(query, (usuario_id,)) # await?
            logger.debug(f"Obtenidos {len(roles)} roles activos (detalle) para usuario ID {usuario_id}.")
            return roles

        except Exception as e:
            logger.exception(f"Error obteniendo roles (detalle) para usuario ID {usuario_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo roles del usuario: {str(e)}")


    @staticmethod
    async def verificar_usuario_existente(nombre_usuario: str, correo: str) -> bool:
        """
        Verifica si ya existe un usuario (activo o inactivo) con el mismo
        nombre de usuario o correo, para prevenir violaciones de UNIQUE constraint.
        Lanza ValidationError (409 Conflict) si existe. Devuelve False si no existe.
        """
        try:
            # --- MODIFICACIÓN: Quitar 'AND es_eliminado = 0' ---
            # Buscar en toda la tabla si la constraint UNIQUE aplica a todos los registros.
            query = """
            SELECT nombre_usuario, correo
            FROM dbo.usuario -- Añadir esquema dbo si es necesario
            WHERE (LOWER(nombre_usuario) = LOWER(?) OR LOWER(correo) = LOWER(?))
            -- AND es_eliminado = 0  <--- ELIMINADO O COMENTADO
            """
            # Pasar los valores en minúsculas para la comparación
            params = (nombre_usuario.lower(), correo.lower())
            # Asumiendo que execute_query es síncrono basado en tu código
            resultados = execute_query(query, params) # await?

            if resultados:
                # Comprobar exactamente qué campo coincide (ya comparado en minúsculas en SQL)
                # Podemos refinar el mensaje si queremos saber cuál coincidió
                nombre_usuario_coincide = any(r['nombre_usuario'].lower() == nombre_usuario.lower() for r in resultados)
                correo_coincide = any(r['correo'].lower() == correo.lower() for r in resultados)

                if nombre_usuario_coincide:
                    # Usar 409 Conflict para duplicados
                    raise ValidationError(status_code=409, detail="El nombre de usuario ya está en uso.")
                if correo_coincide:
                    # Usar 409 Conflict para duplicados
                    raise ValidationError(status_code=409, detail="El correo electrónico ya está registrado.")
                # Si por alguna razón la query SQL devolvió algo pero no coincide exactamente (raro)
                # podríamos lanzar un error genérico 409 aquí, pero los if anteriores deberían cubrirlo.

            # Si no hay resultados, no existe conflicto
            return False
        except ValidationError as e:
            raise e # Re-lanzar validación
        except Exception as e:
            logger.exception(f"Error verificando usuario existente ({nombre_usuario}, {correo}): {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error en la verificación de usuario: {str(e)}")


    @staticmethod
    async def crear_usuario(usuario_data: Dict) -> Dict:
        """
        Crea un nuevo usuario.
        """
        try:
            # 1. Validar que no existan duplicados
            await UsuarioService.verificar_usuario_existente(
                usuario_data['nombre_usuario'],
                usuario_data['correo']
            )

            # 2. Hash de la contraseña
            hashed_password = get_password_hash(usuario_data['contrasena'])

            # 3. Insertar nuevo usuario
            insert_query = """
            INSERT INTO dbo.usuario ( -- Añadir esquema dbo si es necesario
                nombre_usuario, correo, contrasena, nombre, apellido,
                es_activo, correo_confirmado, es_eliminado
            )
            OUTPUT
                INSERTED.usuario_id, INSERTED.nombre_usuario, INSERTED.correo,
                INSERTED.nombre, INSERTED.apellido, INSERTED.es_activo,
                INSERTED.correo_confirmado,
                INSERTED.fecha_creacion
            VALUES (?, ?, ?, ?, ?, 1, 0, 0) -- Valores por defecto
            """
            params = (
                usuario_data['nombre_usuario'],
                usuario_data['correo'],
                hashed_password,
                usuario_data.get('nombre'), # Usar .get() para campos opcionales
                usuario_data.get('apellido')
            )
            result = execute_insert(insert_query, params) # await?

            if not result:
                raise ServiceError(status_code=500, detail="Error creando usuario en la base de datos.")

            logger.info(f"Usuario creado exitosamente con ID: {result.get('usuario_id')}")

            # Opcional: Asignar rol por defecto
            # ... (código para asignar rol por defecto) ...

            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al crear usuario {usuario_data.get('nombre_usuario')}: {e.detail}")
            raise e
        except Exception as e:
            logger.exception(f"Error inesperado al crear usuario {usuario_data.get('nombre_usuario')}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error creando usuario: {str(e)}")


    @staticmethod
    async def actualizar_usuario(usuario_id: int, usuario_data: Dict) -> Dict:
        """
        Actualiza los datos de un usuario existente.
        """
        try:
            # 1. Verificar si el usuario existe
            usuario_existente = await UsuarioService.obtener_usuario_por_id(usuario_id)
            if not usuario_existente:
                raise ValidationError(status_code=404, detail="Usuario no encontrado")

            # 2. Verificar duplicados si se cambian campos únicos
            check_duplicates = False
            if 'nombre_usuario' in usuario_data and usuario_data['nombre_usuario'] != usuario_existente.get('nombre_usuario'):
                check_duplicates = True
            if 'correo' in usuario_data and usuario_data['correo'] != usuario_existente.get('correo'):
                check_duplicates = True

            if check_duplicates:
                verify_query = """
                SELECT usuario_id, nombre_usuario, correo
                FROM dbo.usuario -- Añadir esquema dbo si es necesario
                WHERE (nombre_usuario = ? OR correo = ?)
                AND usuario_id != ? AND es_eliminado = 0
                """
                check_nombre_usuario = usuario_data.get('nombre_usuario', usuario_existente.get('nombre_usuario'))
                check_correo = usuario_data.get('correo', usuario_existente.get('correo'))
                params_verify = (check_nombre_usuario, check_correo, usuario_id)
                duplicados = execute_query(verify_query, params_verify) # await?

                if duplicados:
                    if any(d['nombre_usuario'] == check_nombre_usuario for d in duplicados):
                         raise ValidationError(status_code=400, detail=f"El nombre de usuario '{check_nombre_usuario}' ya está en uso.")
                    if any(d['correo'] == check_correo for d in duplicados):
                         raise ValidationError(status_code=400, detail=f"El correo '{check_correo}' ya está en uso.")

            # 3. Construir la consulta de actualización
            update_parts = []
            params_update = []
            # Campos permitidos para actualizar (excluir contraseña aquí)
            allowed_fields = {'nombre_usuario', 'correo', 'nombre', 'apellido', 'es_activo'}

            for field in allowed_fields:
                if field in usuario_data and usuario_data[field] is not None:
                    # Opcional: verificar si el valor realmente cambió
                    # if usuario_data[field] != usuario_existente.get(field):
                    update_parts.append(f"{field} = ?")
                    params_update.append(usuario_data[field])

            if not update_parts:
                # Si no hay nada que actualizar, devolver los datos existentes o un mensaje
                logger.info(f"No se proporcionaron campos válidos para actualizar para usuario ID {usuario_id}.")
                # return usuario_existente # O lanzar error si se espera una actualización
                raise ValidationError(status_code=400, detail="No hay campos válidos para actualizar")


            update_parts.append("fecha_actualizacion = GETDATE()") # Actualizar fecha
            params_update.append(usuario_id) # Añadir ID para el WHERE

            update_query = f"""
            UPDATE dbo.usuario -- Añadir esquema dbo si es necesario
            SET {', '.join(update_parts)}
            OUTPUT
                INSERTED.usuario_id, INSERTED.nombre_usuario, INSERTED.correo,
                INSERTED.nombre, INSERTED.apellido, INSERTED.es_activo,INSERTED.correo_confirmado,
                INSERTED.fecha_creacion, INSERTED.fecha_actualizacion
            WHERE usuario_id = ? AND es_eliminado = 0
            """
            result = execute_update(update_query, tuple(params_update)) # await?

            if not result:
                # Podría ser que el usuario fue eliminado concurrentemente
                logger.warning(f"No se pudo actualizar el usuario ID {usuario_id}, puede que no exista o esté eliminado.")
                raise ServiceError(status_code=404, detail="Error al actualizar el usuario, no encontrado o no se pudo modificar.")

            logger.info(f"Usuario ID {usuario_id} actualizado exitosamente.")
            return result

        except ValidationError as e:
            logger.warning(f"Error de validación al actualizar usuario ID {usuario_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.exception(f"Error inesperado al actualizar usuario ID {usuario_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error actualizando usuario: {str(e)}")


    @staticmethod
    async def eliminar_usuario(usuario_id: int) -> Dict:
        """
        Realiza un borrado lógico del usuario y desactiva sus roles.
        """
        try:
            # 1. Verificar si el usuario existe y no está eliminado
            # Usar una query simple para verificar existencia y estado
            check_query = "SELECT es_eliminado FROM dbo.usuario WHERE usuario_id = ?"
            user_status = execute_query(check_query, (usuario_id,)) # await?

            if not user_status:
                 raise ValidationError(status_code=404, detail="Usuario no encontrado")
            if user_status[0]['es_eliminado']:
                 logger.info(f"Usuario ID {usuario_id} ya estaba eliminado.")
                 # Devolver un mensaje indicando que ya estaba eliminado
                 return {"message": "Usuario ya estaba eliminado", "usuario_id": usuario_id}


            # 2. Realizar el borrado lógico
            update_query = """
            UPDATE dbo.usuario -- Añadir esquema dbo si es necesario
            SET es_eliminado = 1, es_activo = 0, fecha_actualizacion = GETDATE()
            OUTPUT INSERTED.usuario_id, INSERTED.nombre_usuario, INSERTED.es_eliminado
            WHERE usuario_id = ? AND es_eliminado = 0 -- Condición extra por concurrencia
            """
            result = execute_update(update_query, (usuario_id,)) # await?

            if not result:
                # Podría ser por concurrencia (alguien lo eliminó justo antes)
                logger.warning(f"No se pudo eliminar lógicamente el usuario ID {usuario_id}, posible concurrencia.")
                raise ServiceError(status_code=409, detail="Conflicto al eliminar el usuario, posible concurrencia.")


            # 3. Desactivar asignaciones de roles del usuario eliminado
            try:
                deactivate_roles_query = """
                UPDATE dbo.usuario_rol SET es_activo = 0 -- Añadir esquema dbo si es necesario
                WHERE usuario_id = ? AND es_activo = 1
                """
                # No necesitamos esperar el resultado, pero sí la ejecución si es async
                execute_update(deactivate_roles_query, (usuario_id,)) # await?
                logger.info(f"Roles desactivados para usuario eliminado ID {usuario_id}.")
            except Exception as role_error:
                 logger.error(f"Error desactivando roles para usuario eliminado ID {usuario_id}: {role_error}")
                 # No fallar la eliminación principal por esto, solo loggear

            logger.info(f"Usuario ID {usuario_id} eliminado lógicamente exitosamente.")
            return {
                "message": "Usuario eliminado lógicamente exitosamente",
                "usuario_id": result['usuario_id'],
                "es_eliminado": result['es_eliminado']
            }

        except ValidationError as e:
            logger.warning(f"Error de validación al eliminar usuario ID {usuario_id}: {e.detail}")
            raise e
        except Exception as e:
            logger.exception(f"Error inesperado al eliminar usuario ID {usuario_id}: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error eliminando usuario: {str(e)}")

# --- MÉTODO NUEVO PARA LISTADO PAGINADO ---
    @staticmethod
    async def get_usuarios_paginated(
        # db: pyodbc.Connection, # Descomentar si pasas la conexión directamente
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Dict:
        """
        Obtiene una lista paginada de usuarios (no eliminados) con sus roles activos.
        Permite búsqueda por nombre de usuario, correo, nombre o apellido.

        Args:
            page: Número de página solicitada (empieza en 1).
            limit: Número máximo de usuarios por página.
            search: Término de búsqueda opcional.

        Returns:
            Un diccionario con la estructura de PaginatedUsuarioResponse.

        Raises:
            ServiceError: Si ocurre un error durante la consulta a la BD.
            ValidationError: Si los parámetros de paginación son inválidos.
        """
        logger.info(f"Iniciando get_usuarios_paginated: page={page}, limit={limit}, search='{search}'")

        if page < 1:
            raise ValidationError(status_code=400, detail="El número de página debe ser mayor o igual a 1.")
        if limit < 1:
            raise ValidationError(status_code=400, detail="El límite por página debe ser mayor o igual a 0.")

        offset = (page - 1) * limit
        search_param = f"%{search}%" if search else None # Preparar para LIKE

        try:
            # --- 1. Contar el total de usuarios que coinciden ---
            count_params = (search_param, search_param, search_param, search_param, search_param)
            # NOTA: Asume que execute_query puede ser awaited si es necesario.
            # Si execute_query es síncrono, elimina 'await' y haz el método síncrono.
            count_result = execute_query(COUNT_USUARIOS_PAGINATED, count_params)
            # await execute_query(COUNT_USUARIOS_PAGINATED, count_params) # Si es async

            if not count_result or not isinstance(count_result, list) or len(count_result) == 0:
                 logger.error("Error al contar usuarios: la consulta no devolvió resultados esperados.")
                 raise ServiceError(status_code=500, detail="Error al obtener el total de usuarios.")

            # El resultado de COUNT es una lista con un diccionario, la primera columna sin nombre
            total_usuarios = count_result[0].get('') # pyodbc puede devolver columna sin nombre para COUNT(*)
            if total_usuarios is None:
                 # Intenta obtener por índice si no hay nombre (depende del driver/config)
                 try:
                     total_usuarios = list(count_result[0].values())[0]
                 except IndexError:
                     logger.error(f"No se pudo extraer el total de usuarios del resultado: {count_result[0]}")
                     raise ServiceError(status_code=500, detail="Error al interpretar el total de usuarios.")

            logger.debug(f"Total de usuarios encontrados (sin paginar): {total_usuarios}")

            # --- 2. Obtener los datos paginados de los usuarios y sus roles ---
            data_params = (search_param, search_param, search_param, search_param, search_param, offset, limit)
            # NOTA: Asume que execute_query puede ser awaited si es necesario.
            raw_results = execute_query(SELECT_USUARIOS_PAGINATED, data_params)
            # await execute_query(SELECT_USUARIOS_PAGINATED, data_params) # Si es async

            # --- 3. Procesar los resultados para agrupar roles por usuario ---
            usuarios_dict: Dict[int, UsuarioReadWithRoles] = {}
            if raw_results:
                logger.debug(f"Procesando {len(raw_results)} filas crudas de la base de datos.")
                for row in raw_results:
                    usuario_id = row['usuario_id']
                    if usuario_id not in usuarios_dict:
                        # Crear la entrada del usuario si es la primera vez que lo vemos
                        usuarios_dict[usuario_id] = UsuarioReadWithRoles(
                            usuario_id=row['usuario_id'],
                            nombre_usuario=row['nombre_usuario'],
                            correo=row['correo'],
                            nombre=row.get('nombre'), # Usar .get() por si son NULL
                            apellido=row.get('apellido'),
                            es_activo=row['es_activo'],
                            correo_confirmado=row['correo_confirmado'],
                            fecha_creacion=row['fecha_creacion'],
                            fecha_ultimo_acceso=row.get('fecha_ultimo_acceso'),
                            fecha_actualizacion=row.get('fecha_actualizacion'),
                            roles=[] # Inicializar lista de roles vacía
                        )

                    # Añadir el rol si existe en esta fila (LEFT JOIN puede traer NULLs)
                    if row.get('rol_id') is not None:
                        # Crear objeto RolRead
                        rol_obj = RolRead(
                            rol_id=row['rol_id'],
                            nombre=row['nombre_rol'], # Usamos el alias de la query
                            # Asumimos que la query ya filtró roles inactivos,
                            # pero si no, necesitarías obtener 'es_activo' del rol aquí.
                            # Si necesitas 'descripcion' o 'fecha_creacion' del rol,
                            # añádelos a la query SELECT_USUARIOS_PAGINATED
                            descripcion=None, # O obtener de la query si se añadió
                            es_activo=True, # Asumido por el filtro de la query
                            fecha_creacion=datetime.now() # Placeholder, obtener de la query si se añadió
                        )
                        # Evitar duplicados si la query devuelve la misma combinación user/rol varias veces
                        if rol_obj not in usuarios_dict[usuario_id].roles:
                             usuarios_dict[usuario_id].roles.append(rol_obj)

            lista_usuarios_procesados = list(usuarios_dict.values())
            logger.debug(f"Procesados {len(lista_usuarios_procesados)} usuarios únicos.")

            # --- 4. Calcular total de páginas ---
            total_paginas = math.ceil(total_usuarios / limit) if limit > 0 else 0

            # --- 5. Construir el diccionario de respuesta final ---
            response_data = {
                "usuarios": [u.model_dump() for u in lista_usuarios_procesados], # Convertir a dicts para la respuesta
                "total_usuarios": total_usuarios,
                "pagina_actual": page,
                "total_paginas": total_paginas
            }

            # Validar con Pydantic (opcional pero recomendado para asegurar consistencia)
            # try:
            #     PaginatedUsuarioResponse(**response_data)
            # except Exception as pydantic_error:
            #     logger.error(f"Error de validación Pydantic en la respuesta: {pydantic_error}")
            #     # Podrías lanzar un error aquí o solo loggear

            logger.info(f"get_usuarios_paginated completado exitosamente.")
            return response_data

        except ValidationError as ve:
             logger.warning(f"Error de validación en get_usuarios_paginated: {ve.detail}")
             raise ve # Re-lanzar error de validación
        except Exception as e:
            logger.exception(f"Error inesperado en get_usuarios_paginated: {str(e)}")
            # Considera si quieres exponer detalles del error SQL al cliente
            raise ServiceError(status_code=500, detail=f"Error obteniendo la lista de usuarios: {str(e)}")

# --- FIN DE LA CLASE UsuarioService ---