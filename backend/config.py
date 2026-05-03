from pathlib import Path
import os

# paths
DATASET_PATH: Path = Path("dataset")
ATTENDANCE_DIR: Path = Path("attendance")
ATTENDANCE_CSV: Path = ATTENDANCE_DIR / "attendance.csv"

# database
# Use DATABASE_URL environment variable for PostgreSQL
# Format: postgresql://username:password@localhost:5432/dbname
# Fallback to local SQLite for development only
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///attendance.db"
)

# face detection / recognition
DETECTION_SCALE: float = 0.5
FRAME_SKIP: int = 2
MIN_DETECTION_CONFIDENCE: float = 0.7
EMBEDDING_DISTANCE_THRESHOLD: float = 0.60
MIN_RECOGNITION_CONFIDENCE: float = 0.65

# logging
LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL: str = "INFO"
