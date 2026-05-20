from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# paths
DATASET_PATH: Path = Path(os.getenv("DATASET_PATH", "dataset"))
ATTENDANCE_DIR: Path = Path(os.getenv("ATTENDANCE_DIR", "attendance"))
ATTENDANCE_CSV: Path = ATTENDANCE_DIR / os.getenv("ATTENDANCE_CSV", "attendance.csv")

# database
# Use DATABASE_URL environment variable for PostgreSQL
# Format: postgresql://username:password@host:5432/dbname
# Fallback to local SQLite for development only
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///attendance.db")

# API / frontend
CLOUD_API_URL: str = os.getenv("CLOUD_API_URL", "")
CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

# face detection / recognition
DETECTION_SCALE: float = float(os.getenv("DETECTION_SCALE", 0.5))
FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", 2))
MIN_DETECTION_CONFIDENCE: float = float(os.getenv("MIN_DETECTION_CONFIDENCE", 0.7))
EMBEDDING_DISTANCE_THRESHOLD: float = float(os.getenv("EMBEDDING_DISTANCE_THRESHOLD", 0.60))
MIN_RECOGNITION_CONFIDENCE: float = float(os.getenv("MIN_RECOGNITION_CONFIDENCE", 0.65))

# logging
LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(name)s - %(message)s")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
