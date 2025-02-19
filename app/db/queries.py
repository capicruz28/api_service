from typing import List, Dict, Any
from app.db.connection import get_db_connection
from app.core.exceptions import DatabaseError
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