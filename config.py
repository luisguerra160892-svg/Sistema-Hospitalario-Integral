import os
from datetime import timedelta

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-hospital-2025'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///hospital.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT para API móvil
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secreto-hospital-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@hospital.cu')
    
    # Uploads
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Backup
    BACKUP_DIR = 'backups'
    BACKUP_RETENTION_DAYS = 30
    
    # Laboratorio
    LAB_API_KEY = os.environ.get('LAB_API_KEY', 'default-lab-key')
    
    # Seguridad
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    WTF_CSRF_ENABLED = True
    
    # Logging
    LOG_FILE = 'logs/hospital.log'
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}