from typing import List, Dict, Optional
from app.db.queries import execute_query, execute_procedure_params
from app.core.exceptions import ServiceError, ValidationError
from app.schemas.empleado import EmpleadoBusquedaParams
import logging

logger = logging.getLogger(__name__)

class EmpleadoService:
    @staticmethod
    async def get_all_empleados() -> List[Dict]:
        try:
            query = "SELECT * FROM pdgaop00 where nordpr='230152'"
            return execute_query(query)
        except Exception as e:
            logger.error(f"Error obteniendo empleados: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo empleados: {str(e)}")

    @staticmethod
    async def get_plan_cuotas(nordpr: str) -> List[Dict]:
        if not nordpr.isalnum() or not (5 <= len(nordpr) <= 6):
            raise ValidationError(
                status_code=400,
                detail="El número de orden debe ser alfanumérico y tener entre 5 y 6 caracteres"
            )

        try:
            return execute_procedure_params("sp_plan_cuotas_op_api", {"wnordpr": nordpr})
        except Exception as e:
            logger.error(f"Error obteniendo plan de cuotas: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error obteniendo plan de cuotas: {str(e)}")

    @staticmethod
    async def buscar_por_codigo(codigo: str) -> List[Dict]:
        if not codigo.isalnum() or len(codigo) < 2:
            raise ValidationError(
                status_code=400,
                detail="El código debe ser alfanumérico y tener al menos 2 caracteres"
            )

        try:
            query = "SELECT * FROM ousuar00 WHERE LOWER(ctraba) = LOWER(?)"
            return execute_query(query, (codigo,))
        except Exception as e:
            logger.error(f"Error buscando empleado: {str(e)}")
            raise ServiceError(status_code=500, detail=f"Error buscando empleado: {str(e)}")