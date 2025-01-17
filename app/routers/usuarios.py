from fastapi import APIRouter, HTTPException
from app.db.queries import execute_query, execute_procedure

router = APIRouter()

@router.get("/login/{cusuar}/{cclave}")
async def buscar_empleado(cusuar: str, cclave: str):
    # Validación de parámetros alfanuméricos
    if not (cusuar.strip() and cclave.strip()) or len(cusuar) < 2 or len(cclave) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Ambos parámetros deben ser alfanuméricos y tener al menos 2 caracteres"
        )

    # Consulta para búsqueda exacta
    query = """
    SELECT * FROM ousuar00 
    WHERE cusuar = ? AND cclave = ?
    """
    params = (cusuar, cclave)

    try:
        resultados = execute_query(query, params)
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron empleados")
        return {"data": resultados}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")