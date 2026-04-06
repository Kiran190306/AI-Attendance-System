"""Configuration template for face recognition system."""

# Face Recognition Configuration
# ==============================

# Embeddings-based matching threshold (Euclidean distance)
# Lower value = stricter matching = fewer false positives
# Range: 0.5 - 0.7
# Default: 0.60
EMBEDDING_DISTANCE_THRESHOLD = 0.60

# Minimum confidence score for recognition (0-1 scale)
# Lower value = more lenient = more matches
# Range: 0.6 - 0.9
# Default: 0.65
MIN_RECOGNITION_CONFIDENCE = 0.65

# Face detection confidence threshold for MediaPipe
# Range: 0.1 - 1.0
# Default: 0.7
MIN_DETECTION_CONFIDENCE = 0.7

# ==============================
# Real-Time Performance Options
# ==============================

# Process every Nth frame (higher = faster but lower quality)
# 1 = every frame, 2 = every 2nd frame, 3 = every 3rd frame, etc.
# Default: 2
FRAME_SKIP = 2

# Detection resolution scale (0.0 - 1.0)
# Lower = faster detection (1.0 = full resolution, 0.5 = half)
# Default: 0.5
DETECTION_SCALE = 0.5

# Camera capture resolution (width x height)
# Lower = faster processing but lower quality
# Default: 1280x720
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Embedding model for generation ("hog" or "cnn")
# "hog": CPU-efficient, faster
# "cnn": More accurate but slower
# Default: "hog"
EMBEDDING_MODEL = "hog"

# ==============================
# Dataset Configuration
# ==============================

# Dataset root directory
# Each subdirectory should be student name
# Each subdirectory should contain face_*.jpg images
# Default: "dataset"
DATASET_PATH = "dataset"

# Images per student to use for embedding
# Higher = more robust but slower generation
# Default: 10
IMAGES_PER_STUDENT = 10

# ==============================
# Advanced Options
# ==============================

# Enable embeddings caching (faster reload)
# Default: True
ENABLE_CACHING = True

# Cache directory for stored embeddings
# Default: ".embeddings_cache"
CACHE_DIR = ".embeddings_cache"

# Logging level
# Options: "DEBUG", "INFO", "WARNING", "ERROR"
# Default: "INFO"
LOG_LEVEL = "INFO"

# Database persistence
# Default: True (embeddings stored in DB)
PERSIST_TO_DATABASE = True

# Batch processing size for recognition
# Higher = more memory but faster batch operations
# Default: 32
BATCH_SIZE = 32

# ==============================
# How to Use This File
# ==============================

# Option 1: Direct import
# from config import EMBEDDING_DISTANCE_THRESHOLD
# recognizer = OptimizedEmbeddingsRecognizer(
#     match_threshold=EMBEDDING_DISTANCE_THRESHOLD
# )

# Option 2: Environment variables (backend/.env)
# EMBEDDING_DISTANCE_THRESHOLD=0.60
# MIN_RECOGNITION_CONFIDENCE=0.65

# Option 3: Command line arguments
# python attendance_system.py --threshold=0.60 --confidence=0.65

# ==============================
# Tuning Guide
# ==============================

# FOR STRICTER MATCHING (fewer false positives):
# EMBEDDING_DISTANCE_THRESHOLD = 0.55
# MIN_RECOGNITION_CONFIDENCE = 0.70

# FOR MORE LENIENT MATCHING (more recognitions):
# EMBEDDING_DISTANCE_THRESHOLD = 0.65
# MIN_RECOGNITION_CONFIDENCE = 0.60

# FOR FASTER PERFORMANCE:
# FRAME_SKIP = 3
# DETECTION_SCALE = 0.4
# CAMERA_WIDTH = 640
# CAMERA_HEIGHT = 480

# FOR BETTER ACCURACY:
# FRAME_SKIP = 1
# DETECTION_SCALE = 1.0
# CAMERA_WIDTH = 1920
# CAMERA_HEIGHT = 1080
# EMBEDDING_MODEL = "cnn"

# ==============================
# Database Schema
# ==============================

# Student.face_embedding: bytes (512 bytes for 128-d float32)
# Student.embeddings_count: int (number of source images)
# Student.embeddings_updated_at: datetime (last update)

# To list configuration in Python:
# python -c "from config import *; import sys; [print(f'{k}={v}') for k,v in sys.modules[__name__].__dict__.items() if k.isupper()]"
