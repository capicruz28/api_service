import pyodbc
from app.core.config import settings
from contextlib import contextmanager
import logging
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """
    Context manager MUY SIMPLE para obtener y cerrar una conexión a BD.
    Permite que TODOS los errores (conexión u operación) se propaguen.
    """
    conn = None
    try:
        # Intentar conectar. Si falla, pyodbc.Error se propagará.
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.DB_SERVER},{settings.DB_PORT};"
            f"DATABASE={settings.DB_DATABASE};"
            f"UID={settings.DB_USER};"
            f"PWD={settings.DB_PASSWORD};"
            "TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        logger.debug("Conexión a BD establecida.")
        # Entregar la conexión
        yield conn
        # Si el 'with' termina sin error, no hacemos nada aquí

    # NO hay bloque 'except' aquí. Los errores se propagan.
    finally:
        # Asegurar el cierre si la conexión se estableció
        if conn:
            conn.close()
            logger.debug("Conexión a BD cerrada.")

#@contextmanager
#def get_db_connection():
#    conn = None
#    try:
#        conn = pyodbc.connect(
#           f"DRIVER={{ODBC Driver 17 for SQL Server}};"
#            f"SERVER={settings.DB_SERVER},{settings.DB_PORT};"
#            f"DATABASE={settings.DB_DATABASE};"
#            f"UID={settings.DB_USER};"
#            f"PWD={settings.DB_PASSWORD};"
#            "TrustServerCertificate=yes;"
#        )
#        yield conn
#    except pyodbc.Error as e:
#        logger.error(f"Error de conexión a la base de datos: {str(e)}")
#        raise DatabaseError(status_code=500, detail=f"Error de conexión: {str(e)}")
#    finally:
#        if conn:
#            conn.close()