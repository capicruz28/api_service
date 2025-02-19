from typing import List, Dict
from app.db.queries import execute_query
from app.core.exceptions import ServiceError, ValidationError
import logging

logger = logging.getLogger(__name__)

class UsuarioService:
    @staticmethod
    async def login(cusuar: str, cclave: str) -> List[Dict]:
        if not (cusuar.strip() and cclave.strip()) or len(cusuar) < 2 or len(cclave) < 2:
            raise ValidationError(
                status_code=400,
                detail="Usuario y contraseña deben tener al menos 2 caracteres"
            )

        try:
            query = """
            SELECT * FROM ousuar00
            WHERE cusuar = ? AND cclave = ?
            """
            resultados = execute_query(query, (cusuar, cclave))

            if not resultados:
                raise ValidationError(
                    status_code=401,
                    detail="Credenciales inválidas"
                )

            return resultados
        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error en login: {str(e)}")