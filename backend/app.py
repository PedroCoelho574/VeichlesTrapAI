from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, flash
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import jwt
import logging
from dotenv import load_dotenv
import uuid

# Importações de módulos locais
from database import DetectionDatabase
from auth import token_required, admin_required, permission_required, generate_token
from ai_models.pipeline import DetectionPipeline

# Configuração inicial
load_dotenv()
app = Flask(__name__)
CORS(app)
db = DetectionDatabase()
pipeline = DetectionPipeline()

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
cameras_db = {}  # Dicionário para armazenar câmeras

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# [Restante das rotas e funções permanece igual...]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)