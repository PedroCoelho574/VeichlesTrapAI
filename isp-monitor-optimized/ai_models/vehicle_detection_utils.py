import cv2

class VehicleDetectionUtils:
    @staticmethod
    def draw_detections(frame, detections):
        """Draw detection boxes and labels on frame"""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Draw label
            label = f"{det['class_name']} {det['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        return frame

    @staticmethod
    def format_metrics(metrics):
        """Format performance metrics for display"""
        return {
            'fps': 1 / metrics['avg_processing_time'] if metrics['avg_processing_time'] > 0 else 0,
            'avg_processing_time_ms': metrics['avg_processing_time'] * 1000,
            'total_frames_processed': metrics['total_frames']
        }