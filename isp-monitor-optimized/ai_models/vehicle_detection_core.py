import cv2
import numpy as np
import time
from ultralytics import YOLO

class VehicleDetectorCore:
    def __init__(self, model_path='yolov8m.pt', conf_threshold=0.5):
        """Core vehicle detection logic"""
        try:
            self.model = YOLO(model_path)
            self.conf_threshold = conf_threshold
            self.classes = {
                2: 'car',
                3: 'motorcycle', 
                5: 'bus',
                7: 'truck'
            }
            self._reset_metrics()
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def _reset_metrics(self):
        """Initialize performance tracking metrics"""
        self.metrics = {
            'total_frames': 0,
            'avg_processing_time': 0,
            'last_processing_time': 0
        }

    def detect(self, frame):
        """Detect vehicles in a frame and return bounding boxes"""
        start_time = time.time()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model(frame_rgb)
        
        # Update performance metrics
        processing_time = time.time() - start_time
        self.metrics['last_processing_time'] = processing_time
        self.metrics['total_frames'] += 1
        self.metrics['avg_processing_time'] = (
            (self.metrics['avg_processing_time'] * (self.metrics['total_frames'] - 1) + processing_time) 
            / self.metrics['total_frames']
        )
        
        vehicles = []
        for result in results:
            for box in result.boxes:
                if int(box.cls) in self.classes and float(box.conf) >= self.conf_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    vehicles.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(box.conf),
                        'class_id': int(box.cls),
                        'class_name': self.classes[int(box.cls)]
                    })
        
        return vehicles

    def get_metrics(self):
        """Return current performance metrics"""
        return self.metrics