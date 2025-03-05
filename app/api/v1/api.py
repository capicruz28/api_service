from fastapi import APIRouter
from app.api.v1.endpoints import usuarios, auth, menus

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticación"]
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