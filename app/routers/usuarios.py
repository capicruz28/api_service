from fastapi import APIRouter, HTTPException
from app.db.queries import execute_query

router = APIRouter() # 1. Creamos un enrutador para definir las rutas de la API

@router.get("/login/{cusuar}/{cclave}") # 2. Definimos un endpoint GET en "/login/{cusuar}/{cclave}"
async def buscar_empleado(cusuar: str, cclave: str):
        
    if not (cusuar.strip() and cclave.strip()) or len(cusuar) < 2 or len(cclave) < 2: # 3. Verificamos que los parámetros no estén vacíos y tengan al menos 2 caracteres
        raise HTTPException(
            status_code=400, # 4. Si no se cumplen las condiciones, devolvemos un error 400 (Bad Request)
            detail="Ambos parámetros deben ser alfanuméricos y tener al menos 2 caracteres"
        )
    
    # 5. Definimos la consulta SQL para buscar un usuario por su código de usuario y contraseña        
    query = """
    SELECT * FROM ousuar00 
    WHERE cusuar = ? AND cclave = ?
    """
    params = (cusuar, cclave) # 6. Parámetros para la consulta

    try:        
        resultados = execute_query(query, params) # 7. Ejecutamos la consulta
        
        # 8. Si no hay resultados, significa que el usuario no existe o la contraseña es incorrecta
        if not resultados:
            raise HTTPException(status_code=404, detail="No se encontraron usuarios") # 9. Devolvemos un error 404 (Not Found)
                                
        return {"data": resultados} # 10. Si hay resultados, devolvemos la información del usuario encontrado
            
        # 11. Si ocurre un error en la base de datos, devolvemos un error 500 (Internal Server Error)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}") # Error 500: Internal Server Error