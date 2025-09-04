import pyodbc
from app.core.config import settings
from contextlib import contextmanager
import logging
from app.core.exceptions import DatabaseError
from enum import Enum

logger = logging.getLogger(__name__)

class DatabaseConnection(Enum):
    DEFAULT = "default"
    ADMIN = "admin"

def test_drivers():
    """Función para probar qué drivers están disponibles"""
    try:
        drivers = pyodbc.drivers()
        logger.info(f"Drivers ODBC disponibles: {list(drivers)}")
        return drivers
    except Exception as e:
        logger.error(f"Error obteniendo drivers: {e}")
        return []

def get_connection_string(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> str:
    """
    Obtiene la cadena de conexión según el tipo de conexión requerida.
    Intenta múltiples drivers en orden de preferencia.
    """
    try:
        # Obtener drivers disponibles
        available_drivers = test_drivers()
        
        # Lista de drivers en orden de preferencia
        preferred_drivers = [
            'ODBC Driver 18 for SQL Server',
            'ODBC Driver 17 for SQL Server',
            'ODBC Driver 13 for SQL Server',
            'FreeTDS'
        ]
        
        # Encontrar el primer driver disponible
        selected_driver = None
        for driver in preferred_drivers:
            if driver in available_drivers:
                selected_driver = driver
                break
        
        if not selected_driver:
            logger.error(f"No se encontró ningún driver SQL Server compatible. Disponibles: {available_drivers}")
            # Intentar con el driver por defecto anyway
            selected_driver = 'ODBC Driver 17 for SQL Server'
        
        logger.info(f"Usando driver: {selected_driver}")
        
        # Obtener parámetros de conexión según el tipo
        if connection_type == DatabaseConnection.ADMIN:
            server = settings.DB_ADMIN_SERVER
            port = settings.DB_ADMIN_PORT
            database = settings.DB_ADMIN_DATABASE
            user = settings.DB_ADMIN_USER
            password = settings.DB_ADMIN_PASSWORD
        else:
            server = settings.DB_SERVER
            port = settings.DB_PORT
            database = settings.DB_DATABASE
            user = settings.DB_USER
            password = settings.DB_PASSWORD
        
        # Construir connection string según el driver
        if selected_driver == 'FreeTDS':
            conn_str = (
                f"DRIVER={{{selected_driver}}};"
                f"SERVER={server};"
                f"PORT={port};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password};"
                f"TDS_Version=8.0;"
            )
        else:
            conn_str = (
                f"DRIVER={{{selected_driver}}};"
                f"SERVER={server},{port};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=30;"
            )
        
        # Log de debugging (sin mostrar contraseña)
        safe_conn_str = conn_str.replace(f"PWD={password}", "PWD=***")
        logger.info(f"Connection string ({connection_type.value}): {safe_conn_str}")
        
        return conn_str
        
    except Exception as e:
        logger.error(f"Error construyendo connection string: {e}")
        raise DatabaseError(status_code=500, detail=f"Error en configuración de BD: {str(e)}")

@contextmanager
def get_db_connection(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT):
    """
    Context manager para obtener y cerrar una conexión a BD.
    Permite especificar el tipo de conexión requerida.
    """
    conn = None
    try:
        # Verificar configuración básica
        if connection_type == DatabaseConnection.ADMIN:
            if not all([settings.DB_ADMIN_SERVER, settings.DB_ADMIN_USER, settings.DB_ADMIN_PASSWORD]):
                raise DatabaseError(
                    status_code=500, 
                    detail="Configuración de BD admin incompleta"
                )
        else:
            if not all([settings.DB_SERVER, settings.DB_USER, settings.DB_PASSWORD]):
                raise DatabaseError(
                    status_code=500, 
                    detail="Configuración de BD principal incompleta"
                )
        
        conn_str = get_connection_string(connection_type)
        logger.info(f"Intentando conectar a BD ({connection_type.value})...")
        
        # Intentar conexión con timeout
        conn = pyodbc.connect(conn_str, timeout=30)
        logger.info(f"Conexión a BD ({connection_type.value}) establecida exitosamente.")
        
        # Verificar conexión con una consulta simple
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        
        yield conn

    except pyodbc.Error as e:
        error_code = e.args[0] if e.args else 'N/A'
        error_msg = f"Error ODBC ({connection_type.value}): [{error_code}] {str(e)}"
        logger.error(error_msg)
        
        # Mensajes de error más específicos
        if "01000" in str(e):
            logger.error("Error: Driver ODBC no encontrado o no puede cargarse")
        elif "08001" in str(e):
            logger.error("Error: No se puede conectar al servidor SQL Server")
        elif "28000" in str(e):
            logger.error("Error: Credenciales de autenticación inválidas")
        
        raise DatabaseError(status_code=500, detail=f"Error de conexión BD: {str(e)}")
        
    except Exception as e:
        error_msg = f"Error inesperado ({connection_type.value}): {str(e)}"
        logger.error(error_msg)
        raise DatabaseError(status_code=500, detail=f"Error inesperado: {str(e)}")

    finally:
        if conn:
            try:
                conn.close()
                logger.debug(f"Conexión a BD ({connection_type.value}) cerrada.")
            except Exception as e:
                logger.warning(f"Error cerrando conexión: {e}")

# Función de utilidad para test de conexión
async def test_database_connection():
    """Función para probar la conexión a la base de datos"""
    try:
        # Primero mostrar información de debug
        drivers = test_drivers()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT GETDATE() as CurrentTime, @@VERSION as SQLVersion")
            result = cursor.fetchone()
            cursor.close()
            return {
                "status": "success",
                "drivers_available": list(drivers),
                "current_time": str(result[0]),
                "sql_version": result[1][:100] + "..." if len(result[1]) > 100 else result[1]
            }
    except Exception as e:
        logger.error(f"Test de conexión falló: {e}")
        drivers = test_drivers()
        return {
            "status": "error",
            "error": str(e),
            "drivers_available": list(drivers),
            "debug_info": {
                "server": settings.DB_SERVER,
                "database": settings.DB_DATABASE,
                "user": settings.DB_USER,
                "port": settings.DB_PORT
            }
        }