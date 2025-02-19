from fastapi import APIRouter
from app.api.v1.endpoints import empleados, usuarios, menus

api_router = APIRouter()

# Incluir todos los routers de los diferentes módulos
api_router.include_router(
    empleados.router,
    prefix="/empleados",
    tags=["Empleados"]
)

api_router.include_router(
    usuarios.router,
    prefix="/usuarios",
    tags=["Usuarios"]
)

api_router.include_router(
    menus.router,
    prefix="/menus",
    tags=["Menus"]
)