from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import logging
from datetime import datetime
from threading import Thread
from queue import Queue
import os
from dotenv import load_dotenv

# Importações locais
from database import DetectionDatabase
from auth import token_required
from ai_models.pipeline import DetectionPipeline

# Configurações iniciais
load_dotenv()
app = Flask(__name__)

# Configuração CORS completa
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

db = DetectionDatabase()
pipeline = DetectionPipeline()

# Sistema de processamento
camera_queue = Queue()
active_cameras = {}
processing_results = {}

def camera_worker():
    while True:
        camera_id, rtsp_url = camera_queue.get()
        try:
            cap = cv2.VideoCapture(rtsp_url)
            active_cameras[camera_id] = True
            
            while active_cameras.get(camera_id, False):
                ret, frame = cap.read()
                if not ret:
                    break
                
                _, detections = pipeline.process_frame(frame)
                db.log_detection(camera_id, frame, detections)
                processing_results[camera_id] = {
                    'last_update': datetime.now(),
                    'detections': detections
                }
                
        except Exception as e:
            logging.error(f"Erro câmera {camera_id}: {str(e)}")
        finally:
            if 'cap' in locals():
                cap.release()

Thread(target=camera_worker, daemon=True).start()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/cameras', methods=['POST'])
@token_required
def add_camera(current_user):
    data = request.get_json()
    if not all([data.get('camera_id'), data.get('rtsp_url')]):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    db.add_camera(data['camera_id'], data.get('location', ''), data['rtsp_url'])
    camera_queue.put((data['camera_id'], data['rtsp_url']))
    return jsonify({'message': 'Câmera adicionada'}), 201

@app.route('/api/detections', methods=['GET'])
@token_required
def get_detections(current_user):
    detections = db.get_recent_detections(
        camera_id=request.args.get('camera_id'),
        limit=min(int(request.args.get('limit', 100)), 1000)
    )
    return jsonify(detections), 200

@app.errorhandler(500)
def handle_500(e):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(502)
def handle_502(e):
    return jsonify({'error': 'Bad gateway'}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', 
            port=8000,
            threaded=True,
            use_reloader=False)