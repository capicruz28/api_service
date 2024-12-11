import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_SERVER = os.getenv("DB_SERVER")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_DATABASE = os.getenv("DB_DATABASE")
    DB_PORT = os.getenv("DB_PORT", 1433)

settings = Settings()