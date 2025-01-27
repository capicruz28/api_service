from fastapi import FastAPI
from app.routers import empleados
from app.routers import usuarios
from app.routers import menus

app = FastAPI()

# Registrar los routers
app.include_router(empleados.router, prefix="/api/empleados", tags=["Empleados"])

app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])

app.include_router(menus.router, prefix="/api/menus", tags=["Menus"])

@app.get("/")
async def root():
    return {"message": "API FastAPI con SQL Server"}

@app.get("/api/test")
async def test_db():
    from app.db.connection import get_db_connection
    try:
        conn = get_db_connection()
        return {"message": "Conexión exitosa"}
    except Exception as e:
        return {"error": str(e)}