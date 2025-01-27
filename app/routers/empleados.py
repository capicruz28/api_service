from fastapi import APIRouter, HTTPException
from app.db.queries import execute_query, execute_procedure_params

router = APIRouter()

@router.get("/")
async def get_empleados():
    query = "SELECT * FROM pdgaop00 where nordpr='230152'"
    try:
        empleados = execute_query(query)
        return {"data": empleados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/procedimiento/{nordpr}")
async def invocar_procedimiento(nordpr: str):
    if not nordpr.isalnum() or not (5 <= len(nordpr) <= 6):
        raise HTTPException(
            status_code=400, detail="El parámetro nordpr debe ser alfanumérico y tener entre 5 y 6 caracteres"
        )

    procedure_name = "sp_plan_cuotas_op_api"
    params = {"wnordpr": nordpr}

    try:
        resultado = execute_procedure_params(procedure_name, params)
        if not resultado:
            raise HTTPException(status_code=404, detail="No se encontraron resultados")
        return {"data": resultado}
    
    except Exception as e:
        print(f"Error completo: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error en el servidor: {str(e)}"
        )
    
@router.get("/empleados/buscar/{codigo}")
async def buscar_empleado(codigo: str):
    # Validación del parámetro alfanumérico
    if not codigo.isalnum() or len(codigo) < 2:
        raise HTTPException(
            status_code=400, detail="El código debe ser alfanumérico y tener al menos 2 caracteres"
        )

    # Consulta para búsqueda exacta
    query = "SELECT * FROM ousuar00 WHERE LOWER(ctraba) = LOWER(?)"
    params = (codigo,)

    try:
        resultados = execute_query(query, params)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron empleados")
        return {"data": resultados}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")    


@router.get("/empleados/buscar/{nordpr}/{ccarub}")
async def buscar_empleado(nordpr: str, ccarub: str):
    # Validación de parámetros alfanuméricos
    if not (nordpr.strip() and ccarub.strip()) or len(nordpr) < 2 or len(ccarub) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Ambos parámetros deben ser alfanuméricos y tener al menos 2 caracteres"
        )

    # Consulta para búsqueda exacta
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
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")