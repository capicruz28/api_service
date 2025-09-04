from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.exceptions import configure_exception_handlers
from app.api.v1.api import api_router
from app.db.connection import get_db_connection
from app.core.logging_config import setup_logging
import logging
from typing import Any

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configurar manejadores de excepciones
    configure_exception_handlers(app)

    # Incluir las rutas de la API v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Middleware para logging de requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any):
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        return response

    return app

# Crear la instancia de la aplicación
app = create_application()

# Rutas base
@app.get("/")
async def root():
    """
    Ruta raíz que muestra información básica de la API
    """
    return {
        "message": "Service API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado de la aplicación y la conexión a la BD
    """
    try:
        # Verificar conexión a la base de datos
        with get_db_connection() as conn:
            if conn:
                db_status = "connected"
            else:
                db_status = "disconnected"
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        db_status = "error"

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": db_status
    }

# Para compatibilidad con el código existente
@app.get("/api/test")
async def test_db():
    try:
        with get_db_connection() as conn:
            if conn:
                return {"message": "Conexión exitosa"}
            else:
                return {"error": "Conexión fallida: objeto de conexión es None"}
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )