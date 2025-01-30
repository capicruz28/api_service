from fastapi import APIRouter, HTTPException
from app.db.queries import execute_procedure
from app.utils.menu_helper import build_menu_tree

router = APIRouter() # 1. Crea un router de FastAPI

@router.get("/getmenu") # 2. Define un endpoint GET en "/getmenu"
async def invocar_procedimiento(): # 3. Define una función asíncrona para invocar el procedimiento almacenado

    procedure_name = "sp_GetFullMenu" # 4. Nombre del procedimiento almacenado a invocar       

    try:
        resultado = execute_procedure(procedure_name) # 5. Ejecuta el procedimiento almacenado

        menu_items = [dict(row) for row in resultado] # 6. Convierte los resultados a una lista de diccionarios
        
        menu_tree = build_menu_tree(menu_items) # 7. Construye el árbol de menú a partir de los resultados

        if not resultado: # 8. Si no hay resultados, devuelve un error 404
            raise HTTPException(status_code=404, detail="No se encontraron resultados") # Error 404: Not Found
        return {"data": menu_tree} # 9. Devuelve el árbol de menú en formato JSON
    
    except Exception as e: # 10. Manejo de errores
        print(f"Error completo: {str(e)}") # Muestra el error en consola
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}" ) # Devuelve un error 500 (Internal Server Error) con el mensaje de error