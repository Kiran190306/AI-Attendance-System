# 🚀 Setup & Deployment Guide

## Installation & Quick Start

### 1. Prerequisites
- Python 3.9+
- Webcam
- 2GB RAM minimum

### 2. Clone & Setup
```bash
cd AI-Attendance-System
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Capture Training Images
```bash
python capture_faces.py
```
- Enter student name
- Press S/SPACE to capture (~25 images)
- Press Q/ESC to quit

**Repeat for each student** (minimum 3 students for meaningful demo)

### 4. Run the System
```bash
python run_system.py
```

This starts:
- ✅ SQLite database
- ✅ FastAPI backend (http://localhost:8000)
- ✅ Real-time face detection
- ✅ Web dashboard (auto-opens)

## API Endpoints

### Students
```
GET  /api/v1/students              # List all
POST /api/v1/students              # Create
GET  /api/v1/students/{id}         # Get one
PUT  /api/v1/students/{id}         # Update
DEL  /api/v1/students/{id}         # Delete
```

### Attendance
```
GET  /api/v1/attendance/today      # Today's records
GET  /api/v1/attendance            # Date range (query: start_date, end_date)
GET  /api/v1/attendance/summary    # Statistics
GET  /api/v1/attendance/student/{name}  # Student history
```

## Configuration

### Performance Settings (.env)
```bash
# For slow CPU / demo
FRAME_SKIP=3
TARGET_FRAME_WIDTH=480
DETECTION_SCALE=0.25

# For good CPU / production
FRAME_SKIP=1
TARGET_FRAME_WIDTH=640
DETECTION_SCALE=0.5
```

## Troubleshooting

#### dlib Installation Failed
```bash
# Windows: Download pre-built wheel
# Linux: sudo apt-get install build-essential cmake
pip install dlib
```

#### Camera Not Detected
- Close other apps using camera
- Try camera_id=1 or 2 in config
- Check OS permissions

#### No Faces Detected
- ✅ 15+ clear images per student
- ✅ Good lighting in both training and detection
- ✅ Face directly facing camera
- ✅ Dataset folder created correctly

## Production Deployment

### Docker
```bash
docker build -t attendance .
docker run -dp 8000:8000 \
  -v $(pwd)/dataset:/app/dataset \
  -v $(pwd)/attendance:/app/attendance \
  attendance
```

### Environment Variables
```bash
DATABASE_URL=sqlite:///./attendance_system.db
DATASET_PATH=./dataset
MIN_DETECTION_CONFIDENCE=0.7
LOG_LEVEL=INFO
```

## Database

### SQLite (Default)
- **File:** `attendance_system.db`
- **Tables:** students, attendance_logs
- **Backup:** CSV in `attendance/` folder

### PostgreSQL (Production)
```python
# Change in app/database/db.py
DATABASE_URL = "postgresql://user:pass@localhost/attendance"
```

## Performance Monitoring

Check system stats in dashboard or via API:
```bash
curl http://localhost:8000/health
```

Expected metrics:
- FPS: 15-30
- Memory: 500MB-1GB
- CPU: 20-40% on typical hardware

## Documentation

- **API Docs:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **Dashboard:** http://localhost:8000/

## Support

Check logs for detailed info:
```bash
# Terminal output has full logs
# Check database directly
sqlite3 attendance_system.db
sqlite> SELECT * FROM attendance_logs;
```
