import os
from dotenv import load_dotenv

# Load .env from the same directory as this config file
_basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(_basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Fix for Hugging Face or some DB providers:
    # 1. Force use of pymysql if SQLAlchemy tries to use MySQLdb (which is not installed)
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('mysql://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('mysql://', 'mysql+pymysql://', 1)
        
    # 2. Remove ssl-mode which pymysql doesn't like
    if SQLALCHEMY_DATABASE_URI and 'ssl-mode=' in SQLALCHEMY_DATABASE_URI:
        import re
        SQLALCHEMY_DATABASE_URI = re.sub(r'[&?]ssl-mode=[^&]*', '', SQLALCHEMY_DATABASE_URI)
    
    if not SQLALCHEMY_DATABASE_URI:
        # Fallback to sqlite for local dev if no DATABASE_URL is set
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'instance', 'psicologia.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    SCHEDULER_API_ENABLED = True
    
    # Flask-Mail Configuration
    MAIL_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('SMTP_USER')
    MAIL_PASSWORD = os.environ.get('SMTP_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('SMTP_USER')
    MAIL_SUPPRESS_SEND = False
