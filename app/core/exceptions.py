from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class CustomException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class DatabaseError(CustomException):
    pass

class ValidationError(CustomException):
    pass

class NotFoundError(CustomException):
    pass

class ServiceError(CustomException):  # Añadimos la clase ServiceError
    pass

def configure_exception_handlers(app: FastAPI):
    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Error no manejado: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )