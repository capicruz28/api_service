from fastapi import APIRouter, HTTPException
from app.db.queries import execute_query
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/login/{cusuar}/{cclave}")
async def login_usuario(cusuar: str, cclave: str):
    if not (cusuar.strip() and cclave.strip()) or len(cusuar) < 2 or len(cclave) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ambos parámetros deben ser alfanuméricos y tener al menos 2 caracteres"
        )

    query = """
    SELECT * FROM ousuar00
    WHERE cusuar = ? AND cclave = ?
    """
    params = (cusuar, cclave)

    try:
        resultados = execute_query(query, params)
        if not resultados:
            raise HTTPException(
                status_code=404,
                detail="Credenciales inválidas o usuario no encontrado"
            )
        return {"data": resultados}
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar la consulta: {str(e)}"
        )