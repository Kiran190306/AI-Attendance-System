# Render Deployment Guide

## Quick Start

This project uses a **hybrid architecture** where:
- **Cloud Backend** (Render): Lightweight Flask API - NO AI dependencies
- **Local System**: AI processing with heavy libraries (OpenCV, face-recognition, mediapipe)

### Deployment Steps

1. **Connect GitHub Repository**
   - Push this code to GitHub
   - Connect repository to Render dashboard

2. **Create Web Service on Render**
   ```
   Environment: Python
   Build Command: pip install -r cloud_backend/requirements.txt
   Start Command: gunicorn -w 4 -b 0.0.0.0:$PORT cloud_backend.app:app
   ```

3. **Environment Variables**
   Create `.env` in project root with:
   ```
   FLASK_ENV=production
   ```

4. **Verify Deployment**
   - Health check: `GET /health` → Should return `{"status": "OK"}`
   - Home endpoint: `GET /` → Dashboard HTML

### Why This Works

✅ **cloud_backend/requirements.txt** is lightweight:
- Flask + Flask-CORS: Web framework
- requests: HTTP client
- gunicorn: Production server  
- python-dotenv: Config management
- **Total size**: ~50MB (vs 2GB+ with AI libraries)

✅ **No AI dependencies in cloud backend**:
- No opencv-python
- No face-recognition
- No mediapipe
- No dlib

✅ **Large files excluded from deployment**:
- .renderignore filters out dataset/, models, media files
- Deployment size: ~20-30MB

### Local System (Your Machine)

The main `requirements.txt` includes all AI libraries for local processing:
- opencv-python
- face-recognition
- mediapipe
- dlib
- etc.

**Local system sends only processed attendance records to cloud backend.**

### API Endpoints

#### Attendance Marking
```
POST /api/attendance/mark
Content-Type: application/json

{
  "name": "John Doe",
  "confidence": 0.95,
  "camera_id": "camera_1",
  "timestamp_iso": "2024-01-01T10:30:00",
  "date": "2024-01-01",
  "time": "10:30:00"
}
```

#### Get Statistics
```
GET /api/stats
Returns: {
  "total_records": 150,
  "students_marked_today": 25,
  "records_today": 25,
  "last_updated": "2024-01-01T10:30:00"
}
```

#### Health Check
```
GET /health
Returns: {
  "status": "OK",
  "timestamp": "2024-01-01T10:30:00",
  "service": "AI Attendance System - Cloud Backend"
}
```

### Troubleshooting

**Issue: Module not found errors**
- Ensure `cloud_backend/__init__.py` exists ✓
- Check Python path includes cloud_backend module ✓

**Issue: 413 Payload Too Large**
- This shouldn't happen - we only send attendance records, not images

**Issue: Timeout**
- Cloud backend should be fast (JSON operations only)
- If slow, check database operations

### File Structure

```
cloud_backend/
├── app.py                 (Flask app entry point)
├── requirements.txt       (Lightweight dependencies)
├── Procfile              (Render configuration)
├── routes/
│   └── attendance_routes.py
├── services/
├── templates/
│   └── dashboard.html
├── data/
│   └── attendance.json
└── __init__.py
```

### Monitoring

On Render dashboard:
1. **Logs**: Real-time application logs
2. **Metrics**: CPU, memory, bandwidth usage
3. **Events**: Deployments, restarts, errors

### Cost Optimization

- **Free tier**: ~0.5GB memory - sufficient for this lightweight backend
- **No GPU needed**: Pure JSON/API operations
- **Database**: Optional (currently using JSON files)

---

**Last Updated**: 2024
