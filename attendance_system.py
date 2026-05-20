# legacy entry point - new implementation lives in core package
from core.main import run_attendance as _run_attendance_system
import sys

if __name__ == "__main__":
    sys.exit(_run_attendance_system())

"""Real-time face recognition attendance system with embeddings."""
import cv2
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Try to import face_recognition for embeddings
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    logger.warning("face_recognition not installed. Install with: pip install face-recognition")
    HAS_FACE_RECOGNITION = False

# Configuration
DATASET_PATH = Path("dataset")
ATTENDANCE_CSV = "attendance.csv"
MIN_DETECTION_CONFIDENCE = 0.7
EMBEDDING_DISTANCE_THRESHOLD = 0.60  # Strict threshold for accuracy
MIN_RECOGNITION_CONFIDENCE = 0.65  # 65% confidence minimum
FRAME_SKIP = 2  # Process every Nth frame for performance
DETECTION_SCALE = 0.5  # Scale factor for detection (faster)


class EmbeddingsRecognizer:
    """Real-time face recognizer using embeddings."""
    
    def __init__(self):
        self.student_embeddings: Dict[str, np.ndarray] = {}
        self.marked_students = set()
        # Try to use pre-trained encodings first
        self._use_pretrained = False
        
    def load_embeddings_from_dataset(self):
        """Load embeddings from dataset or pre-trained encodings."""
        # First try to load from pre-trained encodings.pkl
        try:
            from backend.core.face_trainer import get_trainer
            trainer = get_trainer()
            if trainer.encodings_dict:
                self.student_embeddings = trainer.encodings_dict
                self._use_pretrained = True
                logger.info(f"Loaded {len(self.student_embeddings)} pre-trained embeddings")
                return True
        except Exception as e:
            logger.debug(f"Could not load pre-trained encodings: {e}")
        
        # Fallback to loading from dataset directory
        return self._load_from_dataset()
    
    def _load_from_dataset(self):
        """Load and cache embeddings from dataset directory."""
        if not DATASET_PATH.exists():
            logger.warning(f"Dataset path not found: {DATASET_PATH}")
            return False
        
        logger.info(f"Loading face embeddings from {DATASET_PATH}...")
        
        student_dirs = [
            d for d in DATASET_PATH.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        
        if not student_dirs:
            logger.warning("No student directories found in dataset")
            return False
        
        for student_dir in sorted(student_dirs):
            student_name = student_dir.name
            embeddings = []
            
            # Find all face images
            face_images = list(student_dir.glob("*.jpg")) + \
                         list(student_dir.glob("*.jpeg")) + \
                         list(student_dir.glob("*.png"))
            
            if not face_images:
                logger.warning(f"No face images found for {student_name}")
                continue
            
            # Generate embeddings
            for image_path in face_images[:10]:  # Limit to 10 images per student
                try:
                    image = face_recognition.load_image_file(str(image_path))
                    face_locations = face_recognition.face_locations(image, model="hog")
                    
                    # Use only if exactly one face
                    if len(face_locations) == 1:
                        encodings = face_recognition.face_encodings(image, face_locations)
                        if encodings:
                            embeddings.append(np.array(encodings[0], dtype=np.float32))
                except Exception as e:
                    logger.debug(f"Error processing {image_path.name}: {e}")
                    continue
            
            if embeddings:
                # Use average embedding for more robust matching
                avg_embedding = np.mean(embeddings, axis=0, dtype=np.float32)
                self.student_embeddings[student_name] = avg_embedding
                logger.info(
                    f"Loaded {len(embeddings)} embeddings for {student_name}"
                )
            else:
                logger.warning(f"No valid embeddings for {student_name}")
        
        logger.info(f"Successfully loaded embeddings for {len(self.student_embeddings)} students")
        return len(self.student_embeddings) > 0
    
    def recognize_face(
        self,
        face_embedding: np.ndarray,
    ) -> Tuple[Optional[str], float]:
        """
        Recognize face by comparing against stored embeddings.
        
        Returns:
            (student_name or None, confidence 0-1)
        """
        if not self.student_embeddings:
            return None, 0.0
        
        # Compute distances to all students
        min_distance = float("inf")
        best_match = None
        
        for student_name, stored_embedding in self.student_embeddings.items():
            distance = np.linalg.norm(face_embedding - stored_embedding)
            if distance < min_distance:
                min_distance = distance
                best_match = student_name
        
        # Check confidence threshold
        if min_distance <= EMBEDDING_DISTANCE_THRESHOLD:
            confidence = max(0.0, 1.0 - (min_distance / EMBEDDING_DISTANCE_THRESHOLD))
            
            if confidence >= MIN_RECOGNITION_CONFIDENCE:
                return best_match, confidence
        
        return None, 0.0
    
    def mark_attendance(self, student_name: str, confidence: float = 1.0, camera: str = "") -> bool:
        """Mark attendance via API."""
        if student_name in self.marked_students:
            return False
        
        try:
            import requests
            api_url = os.getenv('CLOUD_API_URL') or os.getenv('API_URL') or os.getenv('SERVER_URL') or 'http://localhost:5000'
            endpoint = f"{api_url.rstrip('/')}/api/mark_attendance"
            response = requests.post(endpoint, json={
                'name': student_name,
                'confidence': confidence,
                'camera': camera
            }, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('marked'):
                    self.marked_students.add(student_name)
                    logger.info("Marked attendance: %s", student_name)
                    return True
        except Exception as e:
            logger.exception("Failed to mark attendance via API: %s", e)
        
        return False


def extract_face_embedding(frame_bgr: np.ndarray, face_loc: tuple) -> Optional[np.ndarray]:
    """Extract embedding from a face in the frame."""
    try:
        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # face_loc is (top, right, bottom, left)
        face_locations = [face_loc]
        
        # Extract embedding
        encodings = face_recognition.face_encodings(rgb, face_locations)
        if encodings:
            return np.array(encodings[0], dtype=np.float32)
    except Exception as e:
        logger.debug(f"Error extracting embedding: {e}")
    
    return None


def detect_faces_with_optimization(
    frame_bgr: np.ndarray,
    scale: float = 1.0,
) -> list[tuple[int, int, int, int, float]]:
    """
    Detect faces in frame with optional scaling for performance.
    
    Returns:
        List of (x_min, y_min, x_max, y_max, confidence)
    """
    h, w = frame_bgr.shape[:2]
    
    # Scale frame for faster detection if needed
    if scale < 1.0:
        scaled_frame = cv2.resize(frame_bgr, (int(w * scale), int(h * scale)))
        scale_factor = 1.0 / scale
    else:
        scaled_frame = frame_bgr
        scale_factor = 1.0
    
    # Convert to RGB
    rgb = cv2.cvtColor(scaled_frame, cv2.COLOR_BGR2RGB)
    
    # Use face_recognition for face detection
    face_locations = face_recognition.face_locations(rgb, model="hog")
    
    boxes = []
    for top, right, bottom, left in face_locations:
        # Scale back to original size
        x_min = int(left * scale_factor)
        y_min = int(top * scale_factor)
        x_max = int(right * scale_factor)
        y_max = int(bottom * scale_factor)
        confidence = 0.9  # face_recognition doesn't provide confidence, assume high
        boxes.append((x_min, y_min, x_max, y_max, confidence))
    
    return boxes
    
    return boxes


def run_attendance_system():
    """Run real-time face recognition attendance."""
    # Initialize components
    if not HAS_FACE_RECOGNITION:
        print("ERROR: face_recognition library required. Install with: pip install face-recognition")
        return 1
    
    logger.info("Initializing face recognition attendance system...")
    
    # Load embeddings from dataset
    recognizer = EmbeddingsRecognizer()
    if not recognizer.load_embeddings_from_dataset():
        logger.error("Failed to load embeddings. Ensure dataset exists and contains face images.")
        return 1
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open camera")
        return 1
    
    # Set camera resolution for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    logger.info("Starting real-time attendance (Press 'Q' to quit)...")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            
            frame_count += 1
            
            # Skip frames for performance
            if frame_count % FRAME_SKIP != 0:
                cv2.imshow("Real-Time Face Attendance", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            h, w = frame.shape[:2]
            display_frame = frame.copy()
            
            # Detect faces with optimization
            boxes = detect_faces_with_optimization(
                frame,
                scale=DETECTION_SCALE,
            )
            
            for x_min, y_min, x_max, y_max, det_conf in boxes:
                try:
                    # Extract embedding from face
                    face_loc = (y_min, x_max, y_max, x_min)  # face_recognition format
                    embedding = extract_face_embedding(frame, face_loc)
                    
                    if embedding is None:
                        cv2.rectangle(display_frame, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
                        cv2.putText(
                            display_frame, "Detection failed",
                            (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
                        )
                        continue
                    
                    # Recognize face
                    student_name, confidence = recognizer.recognize_face(embedding)
                    
                    if student_name:
                        # Draw green box for recognized face
                        color = (0, 255, 0)
                        marked = recognizer.mark_attendance(student_name, confidence, "Webcam")
                        status = "✓ Marked" if marked else "✓ Marked"
                        label = f"{student_name} {confidence:.0%}"
                        text = f"Recognized: {label}"
                        
                        cv2.rectangle(display_frame, (x_min, y_min), (x_max, y_max), color, 2)
                        cv2.putText(
                            display_frame, text,
                            (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                        )
                        cv2.putText(
                            display_frame, status,
                            (x_min, y_max + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                        )
                    else:
                        # Draw red box for unknown face
                        color = (0, 0, 255)
                        cv2.rectangle(display_frame, (x_min, y_min), (x_max, y_max), color, 2)
                        cv2.putText(
                            display_frame, "Unknown",
                            (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                        )
                
                except Exception as e:
                    logger.error(f"Error processing face: {e}")
                    continue
            
            # Display stats
            stats_text = f"Students: {len(recognizer.student_embeddings)} | Marked: {len(recognizer.marked_students)}"
            cv2.putText(
                display_frame, stats_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2
            )
            cv2.putText(
                display_frame, "Press 'Q' to quit",
                (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1
            )
            
            cv2.imshow("Real-Time Face Attendance", display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        logger.info(f"Session complete: Marked {len(recognizer.marked_students)} students")
        return 0


if __name__ == "__main__":
    import sys
    exit_code = run_attendance_system()
    sys.exit(exit_code)

