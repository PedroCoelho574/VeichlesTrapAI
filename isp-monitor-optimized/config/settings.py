import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    # Configurações Gerais
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # Banco de Dados
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:admin123@mongodb:27017/isp_monitor?authSource=admin')
    DB_NAME = 'isp_monitor'
    MONGO_CONNECT_TIMEOUT = 5000  # 5 segundos
    MONGO_SERVER_SELECTION_TIMEOUT = 5000
    
    # Autenticação
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-123')
    JWT_EXPIRE_HOURS = 24
    
    # Câmeras
    MAX_CAMERAS = int(os.getenv('MAX_CAMERAS', '5'))
    RTSP_TIMEOUT = 10
    
    # IA
    AI_MODEL_PATH = os.path.join(BASE_DIR, 'ai_models')
    DETECTION_THRESHOLD = 0.7

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False