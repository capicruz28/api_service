import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configura el logging global de la aplicación"""
    # Crear el directorio logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configuración básica del logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Handler para archivo rotativo
            RotatingFileHandler(
                'logs/app.log',
                maxBytes=1024*1024,  # 1MB
                backupCount=5
            ),
            # Handler para consola
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado

    Args:
        name: Nombre del módulo (generalmente __name__)

    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(name)