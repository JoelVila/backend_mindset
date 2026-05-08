import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

class Config:
    # Configuración Base
    DEBUG = os.getenv("DEBUG", "True") == "True"

    # Base de datos PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Llave para JWT o sesiones si la necesitas luego
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
