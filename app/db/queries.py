from typing import List, Dict, Any, Callable
from app.db.connection import get_db_connection
from app.core.exceptions import DatabaseError
import pyodbc
import logging

logger = logging.getLogger(__name__)

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error en execute_query: {str(e)}")
            raise DatabaseError(status_code=500, detail=f"Error en la consulta: {str(e)}")
        finally:
            cursor.close()

def execute_auth_query(query: str, params: tuple = ()) -> Dict[str, Any]:
    """
    Ejecuta una consulta específica para autenticación y retorna un único registro
    """
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if cursor.description is None:
                return None

            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()

            if row:
                return dict(zip(columns, row))
            return None

        except Exception as e:
            logger.error(f"Error en execute_auth_query: {str(e)}")
            raise DatabaseError(status_code=500, detail=f"Error en la autenticación: {str(e)}")
        finally:
            if cursor:
                cursor.close()

def execute_insert(query: str, params: tuple = ()) -> Dict[str, Any]:
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Obtener el ID y datos del registro insertado
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                result = dict(zip(columns, cursor.fetchone()))
            else:
                result = {}
            
            conn.commit()
            logger.info("Inserción exitosa")
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en execute_insert: {str(e)}")
            raise DatabaseError(status_code=500, detail=f"Error en la inserción: {str(e)}")
        finally:
            cursor.close()

def execute_update(query: str, params: tuple = ()) -> Dict[str, Any]:
    """
    Ejecuta una consulta UPDATE y retorna los datos actualizados

    Args:
        query: Consulta SQL UPDATE con OUTPUT
        params: Parámetros para la consulta

    Returns:
        Dict con los datos del registro actualizado
    """
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            # Obtener los datos actualizados si hay OUTPUT en la consulta
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                result = dict(zip(columns, cursor.fetchone()))
            else:
                result = {}

            conn.commit()
            logger.info("Actualización exitosa")
            return result

        except Exception as e:
            conn.rollback()
            logger.error(f"Error en execute_update: {str(e)}")
            raise DatabaseError(
                status_code=500,
                detail=f"Error en la actualización: {str(e)}"
            )
        finally:
            cursor.close()            

def execute_procedure(procedure_name: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"EXEC {procedure_name}")

            results = []
            while True:
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results.extend([dict(zip(columns, row)) for row in cursor.fetchall()])
                if not cursor.nextset():
                    break
            return results
        except Exception as e:
            logger.error(f"Error en execute_procedure: {str(e)}")
            raise DatabaseError(status_code=500, detail=f"Error en el procedimiento: {str(e)}")
        finally:
            cursor.close()

def execute_procedure_params(procedure_name: str, params: dict) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            param_str = ", ".join([f"@{key} = ?" for key in params.keys()])
            query = f"EXEC {procedure_name} {param_str}"

            cursor.execute(query, tuple(params.values()))

            results = []
            while True:
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results.extend([dict(zip(columns, row)) for row in cursor.fetchall()])
                if not cursor.nextset():
                    break
            return results
        except Exception as e:
            logger.error(f"Error en execute_procedure_params: {str(e)}")
            raise DatabaseError(status_code=500, detail=f"Error en el procedimiento: {str(e)}")
        finally:
            cursor.close()

def execute_transaction(operations_func: Callable[[pyodbc.Cursor], None]) -> None:
    """
    Ejecuta operaciones de BD en una transacción.
    Maneja errores de conexión y operación de pyodbc.
    """
    conn = None # Para referencia en logging si es necesario
    cursor = None # Para referencia en logging si es necesario
    try:
        # 'get_db_connection' puede lanzar pyodbc.Error si falla la conexión
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 'operations_func' puede lanzar pyodbc.Error (ej. IntegrityError)
            operations_func(cursor)
            # Si todo va bien, commit
            conn.commit()
            logger.debug("Transacción completada exitosamente.")

    except pyodbc.Error as db_err: # Captura CUALQUIER error de pyodbc
        # El rollback es implícito porque no se hizo commit y la conexión se cerrará.
        logger.error(f"Error de base de datos (pyodbc) en transacción: {db_err}", exc_info=True)
        # Relanzar como DatabaseError genérico para el servicio/endpoint
        raise DatabaseError(status_code=500, detail=f"Error DB en transacción: {str(db_err)}")

    except Exception as e:
        # Captura cualquier otro error inesperado en operations_func
        logger.error(f"Error inesperado (no pyodbc) en transacción: {e}", exc_info=True)
        raise DatabaseError(status_code=500, detail=f"Error inesperado en transacción: {str(e)}")

# Consulta para obtener usuarios paginados con sus roles, filtrando eliminados y buscando
SELECT_USUARIOS_PAGINATED = """
WITH UserRoles AS (
    SELECT
        u.usuario_id,
        u.nombre_usuario,
        u.correo,
        u.nombre,
        u.apellido,
        u.es_activo,
        u.correo_confirmado,
        u.fecha_creacion,
        u.fecha_ultimo_acceso,
        u.fecha_actualizacion,
        r.rol_id,
        r.nombre AS nombre_rol
        -- Añade aquí otros campos de 'usuario' o 'rol' que necesites
    FROM usuario u
    LEFT JOIN usuario_rol ur ON u.usuario_id = ur.usuario_id AND ur.es_activo = 1
    LEFT JOIN rol r ON ur.rol_id = r.rol_id AND r.es_activo = 1
    WHERE
        u.es_eliminado = 0
        AND (? IS NULL OR (
            u.nombre_usuario LIKE ? OR
            u.correo LIKE ? OR
            u.nombre LIKE ? OR
            u.apellido LIKE ?
        ))
)
SELECT * FROM UserRoles
ORDER BY usuario_id -- O el campo por el que prefieras ordenar por defecto
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
"""

# Consulta para contar el total de usuarios que coinciden con la búsqueda y no están eliminados
COUNT_USUARIOS_PAGINATED = """
SELECT COUNT(DISTINCT u.usuario_id)
FROM usuario u
WHERE
    u.es_eliminado = 0
    AND (? IS NULL OR (
        u.nombre_usuario LIKE ? OR
        u.correo LIKE ? OR
        u.nombre LIKE ? OR
        u.apellido LIKE ?
    ));
"""

# --- Consultas de Roles (Existentes - SIN CAMBIOS) ---
# (Asumiendo que tienes aquí tus queries SELECT_ROL_BY_ID, INSERT_ROL, etc.)
# Si no las tienes, deberías añadirlas aquí. Por ejemplo:
SELECT_ROL_BY_ID = "SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion FROM dbo.rol WHERE rol_id = ? AND es_activo = 1"
SELECT_ALL_ROLES = "SELECT rol_id, nombre, descripcion, es_activo, fecha_creacion FROM dbo.rol WHERE es_activo = 1 ORDER BY nombre"
INSERT_ROL = "INSERT INTO dbo.rol (nombre, descripcion, es_activo) OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion, INSERTED.es_activo, INSERTED.fecha_creacion VALUES (?, ?, ?)"
UPDATE_ROL = "UPDATE dbo.rol SET nombre = ?, descripcion = ?, es_activo = ? OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.descripcion, INSERTED.es_activo, INSERTED.fecha_creacion WHERE rol_id = ?"
# Nota: DEACTIVATE_ROL podría ser un caso especial de UPDATE_ROL o una query separada
DEACTIVATE_ROL = "UPDATE dbo.rol SET es_activo = 0 OUTPUT INSERTED.rol_id, INSERTED.nombre, INSERTED.es_activo WHERE rol_id = ? AND es_activo = 1"
REACTIVATE_ROL = """
    UPDATE dbo.rol
    SET
        es_activo = 1
    OUTPUT
        INSERTED.rol_id,
        INSERTED.nombre,
        INSERTED.descripcion,
        INSERTED.es_activo,
        INSERTED.fecha_creacion
    WHERE
        rol_id = ?
        AND es_activo = 0;  -- Solo reactivar si está inactivo
"""
CHECK_ROL_NAME_EXISTS = "SELECT rol_id FROM dbo.rol WHERE LOWER(nombre) = LOWER(?) AND rol_id != ?"


# --- NUEVAS QUERIES PARA PAGINACIÓN DE ROLES ---
COUNT_ROLES_PAGINATED = """
    SELECT COUNT(rol_id) as total -- Añadir alias 'total' para consistencia
    FROM dbo.rol
    WHERE (? IS NULL OR (
        LOWER(nombre) LIKE LOWER(?) OR
        LOWER(descripcion) LIKE LOWER(?)
    ));
    -- Nota: No filtra por es_activo aquí para mostrar todos en mantenimiento
    -- Usamos LOWER() para búsqueda insensible a mayúsculas/minúsculas
"""

SELECT_ROLES_PAGINATED = """
    SELECT
        rol_id, nombre, descripcion, es_activo, fecha_creacion
        -- , fecha_actualizacion -- Descomentar si existe y la quieres mostrar
    FROM
        dbo.rol
    WHERE (? IS NULL OR (
        LOWER(nombre) LIKE LOWER(?) OR
        LOWER(descripcion) LIKE LOWER(?)
    ))
    ORDER BY
        rol_id -- O el campo que prefieras (ej. rol_id)
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
    -- Nota: No filtra por es_activo aquí
    -- Usamos LOWER() para búsqueda insensible a mayúsculas/minúsculas
"""
# --- FIN NUEVAS QUERIES ---

# --- NUEVA CONSULTA PARA MENUS (ADMIN) ---
# Llama a la nueva Stored Procedure que obtiene TODOS los menús
GET_ALL_MENUS_ADMIN = "sp_GetAllMenuItemsAdmin;"


# --- NUEVAS CONSULTAS PARA PERMISOS (RolMenuPermiso) ---

# Selecciona todos los permisos asignados a un rol específico
SELECT_PERMISOS_POR_ROL = """
    SELECT rol_menu_id, rol_id, menu_id, puede_ver, puede_editar, puede_eliminar
    FROM rol_menu_permiso
    WHERE rol_id = ?;
"""

# Elimina TODOS los permisos asociados a un rol específico.
# Se usa antes de insertar los nuevos permisos actualizados.
DELETE_PERMISOS_POR_ROL = """
    DELETE FROM rol_menu_permiso
    WHERE rol_id = ?;
"""

# Inserta un nuevo registro de permiso para un rol y un menú.
# Los parámetros serán (rol_id, menu_id, puede_ver, puede_editar, puede_eliminar)
INSERT_PERMISO_ROL = """
    INSERT INTO rol_menu_permiso (rol_id, menu_id, puede_ver, puede_editar, puede_eliminar)
    VALUES (?, ?, ?, ?, ?);
"""

# --- FIN DE NUEVAS CONSULTAS ---