import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    # Configurações principais
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = False
    
    # Banco de Dados
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:admin123@mongodb:27017/')
    DB_NAME = 'isp_monitor'
    
    # Autenticação
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-key')
    JWT_EXPIRE_HOURS = 24
    
    # Configurações de IA
    AI_MODELS_DIR = os.path.join(BASE_DIR, 'ai_models')
    DETECTION_THRESHOLD = 0.7