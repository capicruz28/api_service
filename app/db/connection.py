import pyodbc
from app.config import settings

def get_db_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.DB_SERVER},{settings.DB_PORT};"
            f"DATABASE={settings.DB_DATABASE};"
            f"UID={settings.DB_USER};"
            f"PWD={settings.DB_PASSWORD};"
        )
        return conn
    except pyodbc.Error as e:
        raise Exception(f"Error al conectar a la base de datos: {e}")