from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from database import DetectionDatabase
from auth import token_required, admin_required, generate_token
import jwt
from ai_models.pipeline import DetectionPipeline
import logging
from dotenv import load_dotenv

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

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Credenciais inválidas'}), 400
    
    if db.verify_credentials(username, password):
        token = generate_token(username)
        return jsonify({'token': token, 'username': username}), 200
    
    return jsonify({'message': 'Credenciais inválidas'}), 401

@app.route('/api/detect/upload', methods=['POST'])
@token_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Processar imagem
            img = cv2.imread(filepath)
            if img is not None:
                _, detections = pipeline.process_frame(img)
                
                # Registrar no banco de dados
                db.log_detection('upload', img, detections)
                
                return jsonify({
                    'status': 'success',
                    'detections': detections,
                    'image_url': f'/uploads/{filename}'
                }), 200
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            return jsonify({'message': 'Erro no processamento da imagem'}), 500
    
    return jsonify({'message': 'Tipo de arquivo não permitido'}), 400

@app.route('/api/cameras', methods=['GET'])
@token_required
def get_cameras():
    cameras = list(db.cameras.find({}, {'_id': 0}))
    return jsonify(cameras), 200

@app.route('/api/cameras', methods=['POST'])
@admin_required
def add_camera():
    data = request.get_json()
    camera_id = data.get('camera_id')
    location = data.get('location')
    rtsp_url = data.get('rtsp_url')
    
    if not all([camera_id, location, rtsp_url]):
        return jsonify({'message': 'Dados incompletos'}), 400
    
    db.add_camera(camera_id, location, rtsp_url)
    return jsonify({'message': 'Câmera adicionada com sucesso'}), 201

@app.route('/api/detections', methods=['GET'])
@token_required
def get_detections():
    camera_id = request.args.get('camera_id')
    limit = int(request.args.get('limit', 100))
    detections = db.get_recent_detections(camera_id=camera_id, limit=limit)
    return jsonify(detections), 200

@app.route('/api/analytics', methods=['GET'])
@token_required
def get_analytics():
    hours = int(request.args.get('hours', 24))
    stats = db.get_camera_stats(hours=hours)
    return jsonify(stats), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

from flask import render_template

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
