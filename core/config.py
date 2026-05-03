from pathlib import Path

# --- paths ---------------------------------------------------------------
DATASET_PATH: Path = Path("dataset")
ATTENDANCE_DIR: Path = Path("attendance")
ATTENDANCE_CSV: Path = ATTENDANCE_DIR / "attendance.csv"
ATTENDANCE_DB: Path = ATTENDANCE_DIR / "attendance.db"

# --- face detection / recognition --------------------------------------
DETECTION_SCALE: float = 0.5                # scale down frame for faster detection
FRAME_SKIP: int = 2                         # process every Nth frame
MIN_DETECTION_CONFIDENCE: float = 0.7       # MediaPipe minimum confidence
EMBEDDING_DISTANCE_THRESHOLD: float = 0.60  # match threshold (lower = stricter)
MIN_RECOGNITION_CONFIDENCE: float = 0.65    # minimum confidence to accept

# --- logging ------------------------------------------------------------
LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL = "INFO"

# --- voice attendance ----------------------------------------------------
# CSV log for voice events (student_name,timestamp,voice_command,status)
VOICE_LOG_CSV: Path = Path("logs") / "voice_events.csv"
# how long to record after prompting the user (seconds)
VOICE_RECORD_DURATION: float = 3.0
# acceptable phrases to confirm presence (lowercase comparison)
VALID_VOICE_PHRASES: list[str] = [
    "present",
    "present sir",
    "i'm here",
    "mark attendance",
]

# --- behavior detection --------------------------------------------------
# how many frames to skip before running behavior analysis
BEHAVIOR_FRAME_SKIP: int = 2
# CSV log for behavior events (camera_id,timestamp,person_id,behavior,confidence)
BEHAVIOR_LOG_CSV: Path = Path("logs") / "behavior_events.csv"
# threshold values for various detectors (stubbed)
# e.g., minimum motion magnitude to flag aggression
BEHAVIOR_AGGRESSION_THRESHOLD: float = 0.7
