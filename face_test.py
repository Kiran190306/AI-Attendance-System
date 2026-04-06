"""Test embeddings-based face recognition in real-time."""
import cv2
import logging
from pathlib import Path
import numpy as np
import mediapipe as mp

from modules.recognition.embeddings_generator import EmbeddingsGenerator
from modules.recognition.optimized_recognizer import OptimizedEmbeddingsRecognizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DATASET_PATH = Path("dataset")
CONFIDENCE_THRESHOLD = 0.65
EMBEDDING_DISTANCE_THRESHOLD = 0.60


def main():
    """Test face recognition with live camera."""
    
    # Initialize recognizer
    try:
        recognizer = OptimizedEmbeddingsRecognizer(
            match_threshold=EMBEDDING_DISTANCE_THRESHOLD,
            confidence_threshold=CONFIDENCE_THRESHOLD,
        )
    except RuntimeError as e:
        logger.error(f"Failed to initialize recognizer: {e}")
        logger.error("Install face_recognition: pip install face-recognition")
        return 1
    
    # Load embeddings from dataset
    logger.info(f"Loading embeddings from {DATASET_PATH}...")
    generator = EmbeddingsGenerator(model="hog")
    embeddings_dict = generator.generate_embeddings_from_dataset(DATASET_PATH)
    
    if not embeddings_dict:
        logger.error("No embeddings generated. Check dataset directory.")
        return 1
    
    recognizer.load_embeddings(embeddings_dict)
    logger.info(f"Loaded embeddings for {len(embeddings_dict)} students")
    
    # Initialize face detection
    mp_face_detection = mp.solutions.face_detection
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Cannot open camera")
        return 1
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    logger.info("Starting face recognition test (Press ESC to exit)")
    
    frame_count = 0
    
    with mp_face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.6,
    ) as face_detection:
        
        while True:
            success, frame = cap.read()
            frame_count += 1
            
            if not success:
                logger.warning("Failed to read frame")
                continue
            
            h, w = frame.shape[:2]
            
            # Detect faces
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb_frame)
            
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Convert to pixel coordinates
                    x_min = max(0, int(bbox.xmin * w))
                    y_min = max(0, int(bbox.ymin * h))
                    x_max = min(w, int((bbox.xmin + bbox.width) * w))
                    y_max = min(h, int((bbox.ymin + bbox.height) * h))
                    
                    try:
                        # Extract embedding
                        import face_recognition
                        
                        face_crop = frame[y_min:y_max, x_min:x_max]
                        rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                        
                        face_locations = face_recognition.face_locations(rgb_crop, model="hog")
                        if not face_locations:
                            continue
                        
                        encodings = face_recognition.face_encodings(rgb_crop, face_locations)
                        if not encodings:
                            continue
                        
                        embedding = np.array(encodings[0], dtype=np.float32)
                        
                        # Recognize face
                        student_name, confidence = recognizer.recognize_face(embedding)
                        
                        if student_name:
                            # Green box for recognized
                            color = (0, 255, 0)
                            label = f"{student_name} ({confidence:.0%})"
                            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
                            cv2.putText(
                                frame, label,
                                (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                            )
                        else:
                            # Red box for unknown
                            color = (0, 0, 255)
                            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
                            cv2.putText(
                                frame, "Unknown",
                                (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                            )
                    
                    except Exception as e:
                        logger.debug(f"Error processing face: {e}")
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2)
            
            # Display stats
            stats = recognizer.get_recognition_stats()
            cv2.putText(
                frame,
                f"Students: {stats['enrolled_students']} | Success: {stats['success_rate']} | "
                f"Time: {stats['avg_recognition_time_ms']:.1f}ms",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1
            )
            cv2.putText(
                frame, "ESC: exit",
                (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1
            )
            
            # Display frame
            cv2.imshow("Face Recognition Test", frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Print final stats
    logger.info("Test complete. Final statistics:")
    stats = recognizer.get_recognition_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    return 0


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)

