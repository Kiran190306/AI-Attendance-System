# Production Architecture & Implementation Guide

## System Components

### 1. Core Services (`backend/app/core/`)

#### DatasetLoader (`dataset_loader.py`)
- **Purpose:** Load and cache face embeddings
- **Features:**
  - Scans `dataset/student_name/` folders
  - Computes 128-d embeddings per image
  - Averages embeddings per student
  - Caches in memory for fast recognition
- **Usage:**
  ```python
  from app.core import DatasetLoader
  loader = DatasetLoader("dataset")
  embeddings = loader.load_embeddings()  # {name: np.array}
  ```

#### FaceEngine (`face_engine.py`)
- **Purpose:** Real-time face detection & recognition
- **Features:**
  - MediaPipe face detection
  - L2 distance matching
  - Performance metrics (FPS, latency)
  - Configurable thresholds
  - **Presence intelligence** – integrates SmartPresenceAnalyzer to monitor
    attention, blinking and duration per person (see below)
- **Process:**
  1. Resize frame
  2. Detect faces (MediaPipe)
  3. Extract embeddings (face_recognition)
  4. Match against student embeddings
  5. Run presence analysis (attention/blink/duration)
  6. Return results with confidence scores and status
- **Usage:**
  ```python
  engine = FaceEngine()
  engine.initialize()
  results, display_frame = engine.process_frame(frame)
  # results: [{"box": (x1,y1,x2,y2), "name": str, "confidence": float,
  #            "status": "Focused"/"Distracted"/"Sleeping",
  #            "presence_time": seconds}]
  ```

#### VoiceEngine (`voice_engine.py`)
- **Purpose:** Prompt for and verify spoken confirmation to augment face-based
  attendance.
- **Features:**
  - Triggers a short microphone recording when a recognized face appears
  - Uses `speech_recognition` to transcribe phrases such as "present"
  - Optionally performs speaker identity matching (stubbed for now)
  - Maintains `logs/voice_events.csv` with statuses (`OK`,
    `Phrase not recognized`, `Voice mismatch`, etc.)
  - Asynchronous operation to avoid blocking video loop
- **Workflow:**
  1. ``request(student_name, callback)`` adds name to pending set
  2. Clip recorded (default 3 s) via `voice_recorder.record_async`
  3. Audio transcribed and phrase verified; identity check performed
  4. Callback invoked with ``(name, command, status, valid)``
  5. UI overlay and attendance service updated accordingly
- **Configuration:**
  - `VOICE_LOG_CSV` – path to CSV file
  - `VOICE_RECORD_DURATION` – clip length in seconds
  - `VALID_VOICE_PHRASES` – list of accepted phrases

#### BehaviorDetector (`behavior/behavior_detector.py`)
- **Purpose:** Analyze human pose and motion to label behavior as NORMAL,
  SUSPICIOUS or AGGRESSIVE.
- **Components:**
  - `PoseAnalyzer` – MediaPipe Pose wrapper for landmark extraction
  - `FightDetector` – heuristics on wrist/arm motion for aggression
  - `AnomalyDetector` – simple position history to flag loitering or repeated
    entries
- **Features:**
  - Runs every `BEHAVIOR_FRAME_SKIP` frames to conserve CPU
  - Returns a label/confidence tuple for each tracked individual
  - Logs non-normal events to `logs/behavior_events.csv`
  - Overlay color codes and text are added by `StreamProcessor`
- **Workflow:**
  1. `StreamProcessor` passes `display_frame`, `person_id`, and bounding box
     to `BehaviorDetector.process()`
  2. Detector optionally crops ROI, analyzes pose, and computes confidences
  3. Returns `(label, confidence)` which is used for overlay and logging
- **Configuration:**
  - `BEHAVIOR_FRAME_SKIP` – frame interval for analysis
  - `BEHAVIOR_LOG_CSV` – path to CSV log
  - `BEHAVIOR_AGGRESSION_THRESHOLD` – threshold for fight detector

#### CameraService (`camera_service.py`)


#### CameraService (`camera_service.py`)
- **Purpose:** Manage camera and real-time attendance marking
- **Features:**
  - Threaded background detection
  - Session tracking
  - Automatic attendance marking
  - Performance stats
- **Usage:**
  ```python
  camera = CameraService(face_engine)
  camera.initialize()
  camera.start_detection_loop(on_attendance_marked=callback)
  ```

#### Multi‑Camera Extension
The platform has been extended with a parallel multi‑camera architecture
suitable for campus‑wide deployment.  The new components live under
`ai_attendance/core` and `ai_attendance/events` and are used by the
`ai_attendance/multi_camera.py` entry point.

* **CameraManager** – loads `config/cameras.json`, starts one
  `StreamProcessor` per source and composes the feeds into a grid window.
* **StreamProcessor** – per‑camera thread performing detection and recognition
  using a shared engine; draws overlays and publishes events.
* **SharedRecognitionEngine** – singleton wrapper around the existing
  `FaceRecognitionEngine` so embeddings are loaded only once.
* **Tracker** – issues temporary tracking IDs and links individuals across
  camera streams if seen within a short time window.
* **EventBus** – simple publish/subscribe queue that decouples camera threads
  from the attendance service and writes `recognition_events.log`.
* **Modified AttendanceService** – now accepts a `camera_id` argument, adds a
  column to CSV, and ignores duplicates across cameras.

#### Crowd Intelligence & Smart Monitoring
The system now performs real‑time people analytics on each camera feed.
Analytics components live under `ai_attendance/analytics` and
`ai_attendance/tracking`.

* **CrowdAnalyzer** – orchestrates person detection (HOG), crowd counting,
  density classification, heatmap generation and alert logging.
* **DensityEstimator** – rule‑based classification (low/medium/high).
* **HeatmapGenerator** – accumulates centroid locations and produces
  colorized overlays showing popular areas.
* **MovementTracker** – naive centroid tracker computing entry/exit rates and
  average dwell time.

Alerts for overcrowding and sudden increases are written to
`logs/crowd_alerts.csv` (columns: `camera_id,timestamp,crowd_count,alert_type`).

Configuration, logging and run instructions are covered in the README
("Multi-Camera Smart Campus Mode").


### 2. Database Layer (`backend/app/database/`)

### Presence Intelligence Modules

The new smart presence subsystem lives under `backend/core` and
`backend/analytics`:

* `attention_detector.py` – uses MediaPipe FaceMesh to estimate head
direction; outputs **Focused** or **Distracted**.
* `blink_detector.py` – computes eye aspect ratio, counts blinks, flags
  prolonged eye closure as **Sleeping**.
* `presence_analyzer.py` – orchestrates tracking (re‑uses `PersonTracker`),
  updates per-ID records, aggregates focus/distraction frames and duration.
  Can export session metrics via `session_metrics()`.
* `tracker.py` – existing OpenCV CSRT/KCF tracker mapping each face to a
  unique ID.
* `analytics/session_logger.py` – appends end‑of‑session metrics to
  `analytics/session_log.csv`.

### Proxy Detection (ProxyGuard)

ProxyGuard augments the recognition pipeline with anti‑spoofing checks:

1. **Face consistency** – maintains multiple embeddings per student via
   `DatasetLoader.load_embeddings_multi()` and validates incoming
   embeddings using `EmbeddingValidator` (distance threshold).
2. **Liveness** – uses `LivenessDetector` (blink/head motion) to reject
   static photos; flagged as `NO_BLINK` if none detected.
3. **Multi‑face alert** – re‑runs MediaPipe face detection inside each box;
   two faces within one bounding box trigger `MULTIPLE_FACES`.
4. **Re‑verification** – after marking attendance for a tracker ID, the
   same ID is checked again after ≥2 s; if the face/embedding changes the
   attempt is logged as `FACE_CHANGED`.
5. **Proxy logging** – events are appended to `logs/proxy_attempts.csv`
   with columns:
   `student_name,timestamp,confidence_score,reason`.

ProxyGuard exposes `analyze(frame, results)` which returns augmented
results including `proxy_status` (`valid`,`suspicious`,`proxy`) and
`proxy_reason`.  The camera service uses these to color overlays and
optionally suppress attendance marking.

Metrics are logged and can be reviewed or exported via the analytics
dashboard along with attendance data.

Metrics are consumed by the analytics dashboard (port 5001) and can be
joined with attendance logs for further reporting.

### 2. Database Layer (`backend/app/database/`)

#### Models (`models.py`)
```python
Student:
  - id (PK)
  - name (UNIQUE)
  - roll_number
  - email
  - created_at, updated_at
  - is_active

AttendanceLog:
  - id (PK)
  - student_name (FK)
  - date (INDEX)
  - timestamp
  - confidence (0-1)
  - UNIQUE(student_name, date)  # Prevent duplicates
```

#### Repository (`repository.py`)
- **StudentRepository:**
  - CRUD operations
  - Query by name/id
  - Soft delete
- **AttendanceRepository:**
  - Create/retrieve attendance
  - Date-range queries
  - Summary statistics
  - Prevent duplicate marking

### 3. API Routes (`backend/app/api/v1/`)

#### Students Endpoints
```
GET  /students              → List all active students
GET  /students/{id}         → Retrieve student
POST /students              → Create new student
PUT  /students/{id}         → Update student
DEL  /students/{id}         → Deactivate student
```

#### Attendance Endpoints
```
GET  /attendance/today              → Today's records
GET  /attendance?start_date=...     → Date range
GET  /attendance/summary            → Statistics
GET  /attendance/student/{name}     → Student history
```

#### Health Endpoint
```
GET  /health                → System status
```

### 4. Web Dashboard (`frontend/dashboard.html`)

**Pages:**
1. **Dashboard** - Real-time stats (present, enrolled, FPS)
2. **Attendance** - History search and CSV export
3. **Students** - Management (view, add, delete)
4. **Reports** - Attendance statistics

**Features:**
- Single-page application (vanilla JS)
- Real-time updates via API polling
- Responsive design
- Student management CRUD

## Data Flow

### Initialization Flow
```
run_system.py
  ├─ init_db()                    # Create tables
  ├─ FaceEngine.initialize()      # Load embeddings (+presence analyzer)
  ├─ FastAPI startup              # Start API server
  └─ CameraService.initialize()   # Open camera (with SmartPresenceAnalyzer)
```

### Attendance Marking Flow
```
Camera Frame
  ├─ resize frame
  ├─ detect faces (MediaPipe)
  ├─ extract embedding (face_recognition)
  ├─ match against students
  ├─ if confidence > threshold:
  │   └─ AttendanceRepository.create()
  │       ├─ store in SQLite
  │       ├─ save to CSV
  │       └─ trigger callback
  └─ display frame with overlay
```

### API Request Flow
```
Client Request
  ├─ Route handler
  ├─ Request validation (Pydantic)
  ├─ Business logic
  ├─ Repository layer
  ├─ Database query
  └─ Response JSON
```

## Web Application Architecture

The system now includes a Flask backend and browser-based dashboard.  The
structure is:

```
AI-Attendance-System
│
├── backend/
│   ├── app.py                # Flask application entry point
│   ├── api/                  # blueprint route modules
│   │   ├── routes_students.py
│   │   ├── routes_attendance.py
│   │   └── routes_system.py
│   └── services/             # business logic layer
│       ├── attendance_service.py  # CSV statistics
│       └── student_service.py     # student listing/management
│
├── frontend/
│   ├── dashboard.html
│   ├── attendance.html
│   ├── students.html
│   └── static/
│       ├── style.css
│       └── dashboard.js
│
├── attendance/
│   └── attendance.csv       # data store for logs
```

### Back-end API

* `GET /api/students` – returns list of student names
* `GET /api/attendance` – all records, optional `date` filter, `download=1` to
  obtain CSV
* `GET /api/attendance/today` – summary object with
  `total_students`, `present_today`, `late_students`
* `GET /api/system/status` – basic health check

#### Mobile API

New endpoints supporting mobile camera clients:

* `POST /api/mobile/attendance` – accepts `image_data` (base64),
  `device_id`, `device_token`; runs recognition, marks attendance, prevents
  duplicates and logs device information.
* `GET /api/mobile/students` – return enrolled names for mobile lookup.
* `GET /api/mobile/status` – simple health response.

Mobile clients hit these endpoints when the user captures a face photo.  The
backend uses the same `FaceRecognitionEngine` instance to identify the
student.  Attendance service deduplication prevents repeat marks even if the
mobile app re‑submits.  Events are appended to `logs/mobile_attendance.log`.

The Flask app serves the static HTML pages and assets via `send_from_directory`.
Business logic is centralized in the `services` layer (CSV parsing, student
lookup).

### Front-end

The dashboard.html page uses vanilla JS and Chart.js to render cards and a
doughnut chart showing present/absent breakdown.  `attendance.html` provides a
log table with download button.  `students.html` lists student names.  Styles
live in `frontend/static/style.css` and script in `frontend/static/dashboard.js`.

### Running

Start the web system with:

```bash
python backend/app.py
```

Then open `http://localhost:5000` in any browser.  The UI will fetch data from
the REST API endpoints and display accordingly.


## Configuration Hierarchy

### 1. Environment Variables (.env)
```bash
DATABASE_URL
DATASET_PATH
MIN_DETECTION_CONFIDENCE
EMBEDDING_DISTANCE_THRESHOLD
# etc.
```

### 2. config.py
```python
# Load from environment
# Provide defaults
# Type validation
```

### 3. Component Initialization
```python
engine = FaceEngine(
    detection_confidence=config.MIN_DETECTION_CONFIDENCE,
    match_threshold=config.EMBEDDING_DISTANCE_THRESHOLD,
    # etc.
)
```

## Performance Optimization Strategies

### 1. Frame Processing
- **Resize early:** Reduce resolution before detection
- **Frame skip:** Process every Nth frame
- **Detection scale:** Downsample for faster detection

### 2. Embedding Caching
- Load all embeddings once on startup
- Keep in memory (not recompute)
- Vectorized L2 distance (numpy)

### 3. Threading
- Camera loop in background thread
- API server in main/separate thread
- Database queries (SQLite is thread-safe)

### 4. Database Optimization
- Index on `date` and `student_name`
- UNIQUE constraint prevents duplicate inserts
- SQLite is lightweight (no server needed)

## Error Handling Strategy

### 1. Component Level
```python
try:
    engine.initialize()
except FaceEngineError as e:
    logger.error(f"Engine init failed: {e}")
    raise
```

### 2. API Level
```python
@router.get("/students")
async def get_students(db = Depends(get_db)):
    try:
        students = StudentRepository.get_all(db)
        return students
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Application Level
```python
try:
    system.initialize()
    system.run()
except KeyboardInterrupt:
    logger.info("User interrupted")
except Exception as e:
    logger.error(f"Fatal error: {e}")
finally:
    system.cleanup()
```

## Database Schema Design

### SQLite Schema (Created Automatically)

```sql
-- Students table
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    roll_number TEXT,
    email TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

-- Attendance logs table
CREATE TABLE attendance_logs (
    id INTEGER PRIMARY KEY,
    student_name TEXT NOT NULL,
    date DATE NOT NULL,
    timestamp DATETIME NOT NULL,
    confidence REAL NOT NULL,
    UNIQUE(student_name, date)
);

CREATE INDEX idx_attendance_date ON attendance_logs(date);
CREATE INDEX idx_attendance_student ON attendance_logs(student_name);
```

### Duplicate Prevention

The `UNIQUE(student_name, date)` constraint ensures:
- Only one attendance record per student per day
- Automatic update if confidence score improves
- Data integrity maintained

## Scalability Considerations

### Current Architecture Limits
- **SQLite:** ~10k records before performance degradation
- **File system:** ~1000 student images before memory issues
- **Single camera:** Sequential processing

### Scaling Strategy
1. **Database:** Migrate to PostgreSQL
2. **API:** Horizontal scaling with load balancer
3. **Processing:** Queue-based batch processing
4. **Storage:** Distributed file system for embeddings
5. **Cache:** Redis for embedding cache

### Example PostgreSQL Migration
```python
# In app/database/db.py
DATABASE_URL = environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://user:pass@localhost:5432/attendance"
)
```

## Security Considerations

### Current Environment
- No authentication (local network)
- No HTTPS (localhost only)
- SQLite with no encryption

### Production Security

#### 1. Authentication
```python
from fastapi import HTTPBearer, Depends

security = HTTPBearer()

@router.get("/students")
async def get_students(credentials: HTTPAuthCredentials = Depends(security)):
    # Verify JWT token
    # Return data
```

#### 2. Environment Secrets
```bash
# .env (never commit)
SECRET_KEY=<random-secret-key>
DATABASE_URL=postgresql://...
API_KEY=<external-service-keys>
```

#### 3. HTTPS
```bash
# Production deployment
uvicorn app.main:app \
  --ssl-keyfile=/path/to/key.pem \
  --ssl-certfile=/path/to/cert.pem
```

#### 4. CORS
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
)
```

## Testing Strategy

### Unit Tests
```python
def test_face_engine_initialization():
    engine = FaceEngine()
    engine.initialize()
    assert len(engine.get_student_list()) > 0

def test_student_repository():
    student = StudentRepository.create(db, "Test Student")
    assert student.name == "Test Student"
    assert StudentRepository.get_by_name(db, "Test Student") is not None
```

### Integration Tests
```python
def test_attendance_marking():
    engine.initialize()
    # Mock face detection
    results = engine.process_frame(mock_frame)
    assert len(results) > 0
    assert results[0]["confidence"] > 0.6
```

### Load Tests
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/v1/students
```

## Monitoring & Logging

### System Metrics
- Frame per second (FPS)
- Detection latency
- Recognition latency
- Database query time
- Memory usage
- CPU usage

### Log Levels
```python
logger.debug("Detailed processing steps")
logger.info("Major events (startup, shutdown)")
logger.warning("Recoverable issues")
logger.error("Errors requiring attention")
```

### Example Log Output
```
2024-01-06 14:30:45 - INFO - Starting database...
✓ Database initialized
✓ Face engine initialized with 5 students
✓ Camera service initialized
2024-01-06 14:30:50 - INFO - Attendance marked: John Doe (confidence: 0.95)
2024-01-06 14:31:12 - INFO - Attendance marked: Jane Smith (confidence: 0.92)
```

## Deployment Checklist

- [ ] All students have 15+ training images
- [ ] Database schema created
- [ ] API documentation accessible
- [ ] Dashboard loads and responds
- [ ] Attendance being marked and saved
- [ ] CSV backup file created
- [ ] Performance metrics acceptable
- [ ] Logs clean (no errors)
- [ ] System stable for 24+ hours

## Recovery & Backup

### Database Backup
```bash
# SQLite backup
cp attendance_system.db attendance_system.db.backup

# Or export to CSV
sqlite3 attendance_system.db ".mode csv" ".output backup.csv" "SELECT * FROM attendance_logs;"
```

### Dataset Backup
```bash
# Backup trained embeddings
cp -r dataset/ dataset_backup/
```

### Recovery
```bash
# Restore database
cp attendance_system.db.backup attendance_system.db

# Re-compute embeddings (if needed)
python run_system.py  # Auto-loads from dataset/
```

---

**Last Updated:** 2024-01-06
**Version:** 1.0.0
**Status:** Production Ready ✅
