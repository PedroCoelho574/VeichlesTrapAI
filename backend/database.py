from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DetectionDatabase:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
        self.db = self.client['isp_vehicle_detection']
        self.detections = self.db['detections']
        self.cameras = self.db['cameras']
        
    def log_detection(self, camera_id, frame_data, vehicles):
        """Store detection results in database"""
        detection_doc = {
            'camera_id': camera_id,
            'timestamp': datetime.now(),
            'isp_vehicle_count': len([v for v in vehicles if v.get('is_isp')]),
            'total_vehicles': len(vehicles),
            'frame_metadata': {
                'width': frame_data.shape[1] if frame_data is not None else None,
                'height': frame_data.shape[0] if frame_data is not None else None
            },
            'vehicles': vehicles
        }
        return self.detections.insert_one(detection_doc)
    
    def get_recent_detections(self, camera_id=None, limit=100):
        """Query recent detections, optionally filtered by camera"""
        query = {'camera_id': camera_id} if camera_id else {}
        return list(self.detections.find(query)
                   .sort('timestamp', -1)
                   .limit(limit))
    
    def add_camera(self, camera_id, location, rtsp_url):
        """Register a new camera in the system"""
        return self.cameras.update_one(
            {'camera_id': camera_id},
            {'$set': {
                'location': location,
                'rtsp_url': rtsp_url,
                'last_active': datetime.now()
            }},
            upsert=True
        )
    
    def get_camera(self, camera_id):
        """Get camera details"""
        return self.cameras.find_one({'camera_id': camera_id})
    
    def update_camera_status(self, camera_id, is_active):
        """Update camera connection status"""
        return self.cameras.update_one(
            {'camera_id': camera_id},
            {'$set': {
                'is_active': is_active,
                'last_active': datetime.now()
            }}
        )

    def get_camera_stats(self, hours=24):
        """Get detection statistics for all cameras"""
        pipeline = [
            {
                '$match': {
                    'timestamp': {
                        '$gte': datetime.now() - timedelta(hours=hours)
                    }
                }
            },
            {
                '$group': {
                    '_id': '$camera_id',
                    'total_detections': {'$sum': 1},
                    'isp_detections': {'$sum': '$isp_vehicle_count'}
                }
            }
        ]
        return list(self.detections.aggregate(pipeline))