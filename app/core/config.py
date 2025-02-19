from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PeruFashions API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API FastAPI para PeruFashions"

    # Database
    DB_SERVER: str = os.getenv("DB_SERVER", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "")
    DB_PORT: int = int(os.getenv("DB_PORT", "1433"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS - Lista predefinida de orígenes permitidos
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "*"
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def get_database_url(self) -> str:
        """
        Construye y retorna la URL de conexión a la base de datos
        """
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.DB_SERVER},{self.DB_PORT};"
            f"DATABASE={self.DB_DATABASE};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD};"
            "TrustServerCertificate=yes;"
        )

    class Config:
        case_sensitive = True

# Instancia de configuración
settings = Settings()