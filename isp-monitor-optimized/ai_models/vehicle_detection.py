import cv2
import numpy as np
from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path='yolov8n.pt'):
        self.model = YOLO(model_path)
        self.classes = [2, 3, 5, 7]  # Car, motorcycle, bus, truck

    def detect(self, frame):
        """Detect vehicles in a frame and return bounding boxes"""
        results = self.model(frame)
        vehicles = []
        
        for result in results:
            for box in result.boxes:
                if int(box.cls) in self.classes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    vehicles.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': float(box.conf),
                        'class_id': int(box.cls)
                    })
        
        return vehicles

    def draw_detections(self, frame, detections):
        """Draw detection boxes on frame"""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{self.model.names[det['class_id']]} {det['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        return frame