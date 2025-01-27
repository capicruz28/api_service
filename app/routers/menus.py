from fastapi import APIRouter, HTTPException
from app.db.queries import execute_query, execute_procedure
from app.utils.menu_helper import build_menu_tree

router = APIRouter()

@router.get("/getmenu")
async def invocar_procedimiento():

    procedure_name = "sp_GetFullMenu"    

    try:
        resultado = execute_procedure(procedure_name)

        # Convertir los resultados a diccionario
        menu_items = [dict(row) for row in resultado]

        # Construir el árbol de menú
        menu_tree = build_menu_tree(menu_items)

        if not resultado:
            raise HTTPException(status_code=404, detail="No se encontraron resultados")
        return {"data": menu_tree}
    
    except Exception as e:
        print(f"Error completo: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error en el servidor: {str(e)}"
        )