from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__) # Instancia de logger

class CustomException(Exception): # Clase base para excepciones personalizadas
    def __init__(self, status_code: int, detail: str): # Constructor
        self.status_code = status_code # Código de estado HTTP
        self.detail = detail # Detalle del error

class DatabaseError(CustomException): # Excepción para errores de base de datos
    pass 

class ValidationError(CustomException): # Excepción para errores de validación
    pass

class NotFoundError(CustomException): # Excepción para errores de recurso no encontrado
    pass

def configure_exception_handlers(app: FastAPI): # Configurar manejadores de excepciones
    @app.exception_handler(CustomException) # Manejador de excepciones personalizadas
    async def custom_exception_handler(request: Request, exc: CustomException): # Manejador de excepciones personalizadas
        return JSONResponse(
            status_code=exc.status_code, # Código de estado HTTP
            content={"detail": exc.detail} # Detalle del error
        )

    @app.exception_handler(Exception) # Manejador de excepciones genéricas
    async def global_exception_handler(request: Request, exc: Exception): # Manejador de excepciones genéricas
        logger.error(f"Error no manejado: {str(exc)}") # Registrar error en el log
        return JSONResponse(
            status_code=500, # Código de estado HTTP
            content={"detail": "Error interno del servidor"} # Detalle del error    
        )