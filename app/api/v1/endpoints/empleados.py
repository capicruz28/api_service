from fastapi import APIRouter, HTTPException
from app.db.queries import execute_query, execute_procedure_params
from app.core.logging_config import get_logger

# Crear el router y el logger
router = APIRouter()
logger = get_logger(__name__)

@router.get("/")
async def get_empleados():
    """
    Obtiene todos los empleados con un nordpr específico
    """
    query = "SELECT * FROM pdgaop00 where nordpr='230152'"
    try:
        empleados = execute_query(query)
        return {"data": empleados}
    except Exception as e:
        logger.error(f"Error al obtener empleados: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/procedimiento/{nordpr}")
async def invocar_procedimiento(nordpr: str):
    """
    Invoca el procedimiento almacenado sp_plan_cuotas_op_api
    """
    if not nordpr.isalnum() or not (5 <= len(nordpr) <= 6):
        raise HTTPException(
            status_code=400,
            detail="El parámetro nordpr debe ser alfanumérico y tener entre 5 y 6 caracteres"
        )

    procedure_name = "sp_plan_cuotas_op_api"
    params = {"wnordpr": nordpr}

    try:
        resultado = execute_procedure_params(procedure_name, params)
        if not resultado:
            raise HTTPException(status_code=404, detail="No se encontraron resultados")
        return {"data": resultado}
    except Exception as e:
        logger.error(f"Error al ejecutar procedimiento: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en el servidor: {str(e)}"
        )

@router.get("/buscar/{codigo}")
async def buscar_empleado(codigo: str):
    """
    Busca un empleado por su código
    """
    if not codigo.isalnum() or len(codigo) < 2:
        raise HTTPException(
            status_code=400,
            detail="El código debe ser alfanumérico y tener al menos 2 caracteres"
        )

    query = "SELECT * FROM ousuar00 WHERE LOWER(ctraba) = LOWER(?)"
    params = (codigo,)

    try:
        resultados = execute_query(query, params)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron empleados")
        return {"data": resultados}
    except Exception as e:
        logger.error(f"Error al buscar empleado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")

@router.get("/buscar/{nordpr}/{ccarub}")
async def buscar_empleado_por_nordpr_ccarub(nordpr: str, ccarub: str):
    """
    Busca empleados por nordpr y ccarub
    """
    if not (nordpr.strip() and ccarub.strip()) or len(nordpr) < 2 or len(ccarub) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ambos parámetros deben ser alfanuméricos y tener al menos 2 caracteres"
        )

    query = """
    SELECT * FROM pdtaop00
    WHERE LOWER(nordpr) = LOWER(?) AND LOWER(ccarub) = LOWER(?)
    """
    params = (nordpr, ccarub)

    try:
        resultados = execute_query(query, params)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron empleados")
        return {"data": resultados}
    except Exception as e:
        logger.error(f"Error al buscar empleado por nordpr y ccarub: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")