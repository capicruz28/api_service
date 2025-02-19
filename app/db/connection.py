import pyodbc
from app.core.config import settings
from contextlib import contextmanager
import logging
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.DB_SERVER},{settings.DB_PORT};"
            f"DATABASE={settings.DB_DATABASE};"
            f"UID={settings.DB_USER};"
            f"PWD={settings.DB_PASSWORD};"
            "TrustServerCertificate=yes;"
        )
        yield conn
    except pyodbc.Error as e:
        logger.error(f"Error de conexión a la base de datos: {str(e)}")
        raise DatabaseError(status_code=500, detail=f"Error de conexión: {str(e)}")
    finally:
        if conn:
            conn.close()