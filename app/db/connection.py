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
    Usa el método del settings para construir la conexión.
    """
    try:
        # Usar el método del config.py
        is_admin = connection_type == DatabaseConnection.ADMIN
        conn_str = settings.get_database_url(is_admin=is_admin)
        
        # Agregar parámetros adicionales recomendados para Azure SQL
        if "Encrypt" not in conn_str:
            conn_str += "Encrypt=yes;"
        if "Connection Timeout" not in conn_str:
            conn_str += "Connection Timeout=30;"
        
        # Log de debugging (sin mostrar contraseña)
        password = settings.DB_ADMIN_PASSWORD if is_admin else settings.DB_PASSWORD
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
        # Verificar drivers disponibles
        drivers = test_drivers()
        
        if 'ODBC Driver 17 for SQL Server' not in drivers:
            logger.error("ODBC Driver 17 for SQL Server no encontrado!")
            logger.error(f"Drivers disponibles: {drivers}")
            raise DatabaseError(
                status_code=500, 
                detail="Driver ODBC para SQL Server no instalado en el sistema"
            )
        
        # Verificar configuración
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
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT GETDATE() as CurrentTime, @@VERSION as SQLVersion")
            result = cursor.fetchone()
            cursor.close()
            return {
                "status": "success",
                "current_time": result[0],
                "sql_version": result[1][:50] + "..." if len(result[1]) > 50 else result[1]
            }
    except Exception as e:
        logger.error(f"Test de conexión falló: {e}")
        return {
            "status": "error",
            "error": str(e)
        }