from flask import Flask
from .config import settings
from .api import init_api
from .services import CameraManager, DetectionService, AlertService
import logging
import atexit

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure application
    app.config.from_object(settings)
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Initialize services
    try:
        camera_manager = CameraManager(max_cameras=app.config['MAX_CAMERAS'])
        detection_service = DetectionService()
        alert_service = AlertService(detection_service)
        
        # Make services available to app context
        app.extensions = {
            'camera_manager': camera_manager,
            'detection_service': detection_service,
            'alert_service': alert_service
        }
        
        # Initialize API
        init_api(app)
        
        # Configure shutdown
        def shutdown_handler():
            logger.info("Shutting down services...")
            camera_manager.stop()
            logger.info("Services stopped")
            
        atexit.register(shutdown_handler)
        
    except Exception as e:
        logger.critical(f"Failed to initialize services: {str(e)}", exc_info=True)
        raise
    
    return app

app = create_app()

if __name__ == '__main__':
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Starting application on {app.config['HOST']}:{app.config['PORT']}")
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
            use_reloader=False
        )
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}", exc_info=True)
