import cv2
import time
from ai_models.vehicle_detection import VehicleDetector
from ai_models.logo_recognition import LogoRecognizer

class DetectionPipeline:
    def __init__(self, vehicle_model='yolov8n.pt', logo_model=None):
        self.vehicle_detector = VehicleDetector(vehicle_model)
        self.logo_recognizer = LogoRecognizer(logo_model)
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()

    def process_frame(self, frame):
        """Process single frame through detection pipeline"""
        # Calculate FPS
        self.frame_count += 1
        if time.time() - self.last_time >= 1:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = time.time()

        # Vehicle detection
        vehicles = self.vehicle_detector.detect(frame)
        isp_vehicles = []
        
        # Logo recognition on detected vehicles
        for vehicle in vehicles:
            x1, y1, x2, y2 = vehicle['bbox']
            vehicle_crop = frame[y1:y2, x1:x2]
            
            if vehicle_crop.size > 0:  # Ensure valid crop
                is_isp = self.logo_recognizer.predict(vehicle_crop)
                if is_isp:
                    vehicle['is_isp'] = True
                    isp_vehicles.append(vehicle)
                    # Draw special marking for ISP vehicles
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(frame, "ISP VEHICLE", (x1, y1-30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        # Draw all detections
        frame = self.vehicle_detector.draw_detections(frame, vehicles)
        
        # Display FPS
        cv2.putText(frame, f"FPS: {self.fps}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        
        return frame, isp_vehicles

    def process_video(self, video_source=0):
        """Process video stream from camera"""
        cap = cv2.VideoCapture(video_source)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            processed_frame, _ = self.process_frame(frame)
            cv2.imshow('ISP Vehicle Detection', processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()