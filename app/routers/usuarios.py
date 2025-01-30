from fastapi import APIRouter, HTTPException
from app.db.queries import execute_query

# Creamos un enrutador para definir las rutas de la API
router = APIRouter()

# Definimos un endpoint GET en "/login/{cusuar}/{cclave}"
@router.get("/login/{cusuar}/{cclave}")
async def buscar_empleado(cusuar: str, cclave: str):
    # 1️. Validación de entrada
    # Verificamos que los parámetros no estén vacíos y tengan al menos 2 caracteres
    if not (cusuar.strip() and cclave.strip()) or len(cusuar) < 2 or len(cclave) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Ambos parámetros deben ser alfanuméricos y tener al menos 2 caracteres"
        )

    # 2️. Consulta SQL segura
    # Definimos la consulta SQL parametrizada para evitar inyección SQL
    query = """
    SELECT * FROM ousuar00 
    WHERE cusuar = ? AND cclave = ?
    """
    params = (cusuar, cclave) # Parámetros para la consulta

    try:        
        resultados = execute_query(query, params) # 3️. Ejecutamos la consulta

        # 4️. Manejo de resultados
        # Si no hay resultados, significa que el usuario no existe o la contraseña es incorrecta
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron empleados")
        return {"data": resultados} # Si hay resultados, devolvemos la información del usuario encontrado
    
        # 5️. Manejo de errores
        # Si ocurre un error en la base de datos, devolvemos un error 500 (Internal Server Error)
    except Exception as e:
        raise HTTPException(status_code=500, # Error 500: Internal Server Error
                            detail=f"Error al ejecutar la consulta: {str(e)}"
                            )