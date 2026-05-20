"""
Face Training Module
Generates and manages face encodings for attendance system
"""

import os
import io
import pickle
import logging
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import cv2
from PIL import Image
import face_recognition

from ..utils import helpers

logger = logging.getLogger(__name__)

class FaceTrainer:
    """Train and manage face encodings"""
    
    DATASET_PATH = Path("dataset")
    ENCODINGS_FILE = DATASET_PATH / "encodings.pkl"
    MIN_IMAGES_PER_STUDENT = 1
    
    def __init__(self):
        self.encodings_dict: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, dict] = {}
        self.load_encodings()
    
    def load_encodings(self) -> bool:
        """Load existing encodings from file"""
        try:
            if Path(self.ENCODINGS_FILE).exists():
                with open(self.ENCODINGS_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.encodings_dict = data.get('encodings', {})
                    self.metadata = data.get('metadata', {})
                logger.info(f"Loaded encodings for {len(self.encodings_dict)} students")
                return True
        except Exception as e:
            logger.error(f"Error loading encodings: {e}")
        
        return False
    
    def save_encodings(self) -> bool:
        """Save encodings to pickle file"""
        try:
            self.ENCODINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'encodings': self.encodings_dict,
                'metadata': self.metadata
            }
            with open(self.ENCODINGS_FILE, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Saved encodings for {len(self.encodings_dict)} students")
            return True
        except Exception as e:
            logger.error(f"Error saving encodings: {e}")
            return False
    
    def train_from_dataset(self) -> Dict[str, any]:
        """Train/retrain from dataset directory"""
        stats = {
            'trained': 0,
            'skipped': 0,
            'failed': 0,
            'students': []
        }
        
        if not self.DATASET_PATH.exists():
            logger.warning(f"Dataset path not found: {self.DATASET_PATH}")
            return stats
        
        student_dirs = [d for d in self.DATASET_PATH.iterdir() 
                       if d.is_dir() and not d.name.startswith('.')]
        
        for student_dir in sorted(student_dirs):
            student_name = student_dir.name
            
            # Find all face images
            images = (list(student_dir.glob('*.jpg')) + 
                     list(student_dir.glob('*.jpeg')) + 
                     list(student_dir.glob('*.png')))
            
            if not images:
                logger.warning(f"No images found for {student_name}")
                stats['skipped'] += 1
                continue
            
            # Generate encodings
            encodings = self._generate_encodings(student_name, images)
            
            if encodings is not None and len(encodings) > 0:
                # Use average encoding for robustness
                avg_encoding = np.mean(encodings, axis=0)
                self.encodings_dict[student_name] = avg_encoding
                self.metadata[student_name] = {
                    'images_count': len(encodings),
                    'training_time': self._get_timestamp()
                }
                stats['trained'] += 1
                stats['students'].append(student_name)
                logger.info(f"Trained {student_name} with {len(encodings)} encodings")
            else:
                stats['failed'] += 1
                logger.error(f"Failed to generate encodings for {student_name}")
        
        # Save after training
        self.save_encodings()
        return stats
    
    def _generate_encodings(self, student_name: str, image_paths: list) -> Optional[list]:
        """Generate face encodings from images"""
        encodings = []
        
        for image_path in image_paths[:10]:  # Limit to 10 images per student
            try:
                # Load image
                image = face_recognition.load_image_file(str(image_path))
                
                # Detect faces
                face_locations = face_recognition.face_locations(image, model='hog')
                
                if len(face_locations) != 1:
                    logger.debug(f"Skipping {image_path.name}: expected 1 face, found {len(face_locations)}")
                    continue
                
                # Generate encoding
                face_encodings = face_recognition.face_encodings(image, face_locations)
                if face_encodings:
                    encodings.append(np.array(face_encodings[0], dtype=np.float32))
                    
            except Exception as e:
                logger.debug(f"Error processing {image_path.name}: {e}")
                continue
        
        return encodings if encodings else None
    
    def add_student(self, student_name: str, image_data: bytes) -> bool:
        """Add a new student with image"""
        student_name = helpers.normalize_student_name(student_name)
        if not student_name:
            logger.error("Invalid student name provided")
            return False

        try:
            # Create student directory
            student_dir = self.DATASET_PATH / student_name
            student_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the next image in the student folder
            image_index = len(list(student_dir.glob('*.jpg'))) + 1
            image_path = student_dir / f"face_{image_index:03d}.jpg"
            
            # Handle image data (could be bytes from PIL or raw bytes)
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = image_data
            
            image = image.convert('RGB')
            image.save(image_path, format='JPEG')
            logger.info(f"Saved image for {student_name} at {image_path}")
            
            # Immediately train this student
            self._train_single_student(student_name)
            
            return True
        except Exception as e:
            logger.error(f"Error adding student {student_name}: {e}")
            return False
    
    def _train_single_student(self, student_name: str) -> bool:
        """Train a single student"""
        try:
            student_dir = self.DATASET_PATH / student_name
            if not student_dir.exists():
                logger.error(f"Student directory not found: {student_dir}")
                return False
            
            images = (list(student_dir.glob('*.jpg')) + 
                     list(student_dir.glob('*.jpeg')) + 
                     list(student_dir.glob('*.png')))
            
            if not images:
                logger.error(f"No images found for {student_name}")
                return False
            
            encodings = self._generate_encodings(student_name, images)
            
            if encodings and len(encodings) > 0:
                avg_encoding = np.mean(encodings, axis=0)
                self.encodings_dict[student_name] = avg_encoding
                self.metadata[student_name] = {
                    'images_count': len(encodings),
                    'training_time': self._get_timestamp()
                }
                self.save_encodings()
                logger.info(f"Trained {student_name}")
                return True
        except Exception as e:
            logger.error(f"Error training {student_name}: {e}")
        
        return False
    
    def recognize_face(self, face_encoding: np.ndarray, threshold: float = 0.6) -> tuple:
        """
        Recognize a face from encoding
        Returns: (student_name, distance)
        """
        if not self.encodings_dict:
            return None, 1.0
        
        min_distance = float('inf')
        best_match = None
        
        for student_name, stored_encoding in self.encodings_dict.items():
            distance = np.linalg.norm(face_encoding - stored_encoding)
            if distance < min_distance:
                min_distance = distance
                best_match = student_name
        
        # Convert distance to confidence (0-1)
        confidence = max(0.0, 1.0 - (min_distance / threshold))
        
        if min_distance <= threshold:
            return best_match, confidence
        
        return None, 0.0
    
    def get_students(self) -> list:
        """Get list of trained students"""
        return list(self.encodings_dict.keys())
    
    def get_stats(self) -> dict:
        """Get training statistics"""
        return {
            'total_students': len(self.encodings_dict),
            'students': self.get_students(),
            'metadata': self.metadata
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Singleton instance
_trainer = None

def get_trainer() -> FaceTrainer:
    """Get or create trainer instance"""
    global _trainer
    if _trainer is None:
        _trainer = FaceTrainer()
    return _trainer
