import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image

class LogoRecognizer:
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._build_model()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                std=[0.229, 0.224, 0.225])
        ])
        
        if model_path:
            self.load_model(model_path)

    def _build_model(self):
        """Create CNN model for logo recognition"""
        model = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(128*28*28, 256),
            nn.ReLU(),
            nn.Linear(256, 2),  # ISP vehicle or not
            nn.Sigmoid()
        )
        return model.to(self.device)

    def load_model(self, path):
        """Load pre-trained weights"""
        self.model.load_state_dict(torch.load(path))
        self.model.eval()

    def preprocess(self, image):
        """Prepare vehicle crop for logo detection"""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        return self.transform(image).unsqueeze(0).to(self.device)

    def predict(self, vehicle_crop):
        """Predict if vehicle belongs to target ISP"""
        with torch.no_grad():
            inputs = self.preprocess(vehicle_crop)
            outputs = self.model(inputs)
            return outputs.squeeze().item() > 0.5  # Returns True if ISP vehicle