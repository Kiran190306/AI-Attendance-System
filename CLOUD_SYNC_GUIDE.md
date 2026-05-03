# Cloud Sync Implementation Guide

## Overview

The AI Attendance System now features **real-time cloud synchronization**. Attendance data marked on the local system is automatically sent to the cloud backend and displayed on a professional web dashboard.

## Architecture

```
┌─────────────────────────────┐
│   Local Attendance System   │
│  (Face Recognition + CSV)   │
└──────────────┬──────────────┘
               │ (POST /api/attendance/mark)
               │ (requests.post)
               ↓
┌─────────────────────────────┐
│   Cloud Backend (Flask)     │
│  (http://localhost:10000)   │
│  (or Render cloud server)   │
└──────────────┬──────────────┘
               │ (GET /api/attendance)
               │ (JavaScript fetch)
               ↓
┌─────────────────────────────┐
│   Web Dashboard             │
│  (Modern UI with Charts)    │
│  (Auto-refresh every 5s)    │
└─────────────────────────────┘
```

## Quick Start

### 1. Run Cloud Backend

```bash
cd cloud_backend
python app.py
```

The server will start on `http://localhost:10000`

```
* Running on http://127.0.0.1:10000
* Running on http://192.168.1.13:10000
```

### 2. Local System Automatically Syncs

When the local attendance system marks a student as present:

```python
# In core/attendance_service.py
attendance_service.mark("John Doe", confidence=0.95)
# ↓ Automatically sends to cloud backend
# POST http://localhost:10000/api/attendance/mark
```

### 3. View Dashboard

Open in browser:
```
http://localhost:10000/dashboard
```

Dashboard updates automatically every 5 seconds with live attendance data.

## Configuration

### Cloud API URL

Configure in `core/cloud_config.py` or via environment variable:

**Local Development (default):**
```python
CLOUD_API_URL = "http://localhost:10000/api/attendance/mark"
```

**Render Cloud Deployment:**
```bash
export CLOUD_API_URL="https://your-app.onrender.com/api/attendance/mark"
```

### Enable/Disable Cloud Sync

```bash
# Enable (default)
export CLOUD_SYNC_ENABLED=true

# Disable (only local recording)
export CLOUD_SYNC_ENABLED=false
```

## API Endpoints

### POST /api/attendance/mark
**Send attendance record from local system to cloud**

```bash
curl -X POST http://localhost:10000/api/attendance/mark \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "date": "2026-04-10",
    "time": "09:30:00",
    "confidence": 0.95,
    "camera_id": "camera_1"
  }'
```

Response:
```json
{
  "status": "success",
  "message": "Attendance marked successfully",
  "record": {
    "name": "John Doe",
    "date": "2026-04-10",
    "time": "09:30:00",
    "confidence": 0.95,
    "camera_id": "camera_1"
  }
}
```

### GET /api/attendance
**Fetch all attendance records (paginated)**

```bash
curl "http://localhost:10000/api/attendance?limit=50&offset=0"
```

### GET /api/attendance/today
**Fetch today's attendance records**

```bash
curl "http://localhost:10000/api/attendance/today"
```

### GET /api/stats
**Get attendance statistics**

```bash
curl "http://localhost:10000/api/stats"
```

Response:
```json
{
  "status": "ok",
  "total_records": 45,
  "students_marked_today": 32,
  "records_today": 42
}
```

## Testing Cloud Sync

Run the included test script:

```bash
python test_cloud_sync.py
```

Output:
```
============================================================
🎓 AI Attendance System - Cloud Sync Demo
============================================================

1️⃣  Sending test attendance records...

📤 Sending attendance for: John Doe
   ✅ Success! Status: success

📤 Sending attendance for: Jane Smith
   ✅ Success! Status: success

2️⃣  Fetching attendance data from cloud...

📊 Current attendance data:
   Total records: 3
   - John Doe at 09:30:00 (confidence: 98.0%)
   - Jane Smith at 09:35:00 (confidence: 95.0%)
```

## How It Works

### Local System Flow

1. **Face Detected** → Attendance marked locally in CSV
2. **Cloud Sync (Async)** → Sends POST request to cloud API
3. **Success or Fail Silently** → Local record always saved, cloud is optional

```python
# core/attendance_service.py
def mark(self, student_name, confidence=1.0, camera_id=None):
    # 1. Normalize and validate
    # 2. Write to local CSV
    # 3. Attempt cloud sync (non-blocking)
    sync_to_cloud(name, date, time, confidence, camera_id)
    return True
```

### Cloud Backend Flow

1. **Receive POST** → `/api/attendance/mark`
2. **Validate & Store** → In-memory (ATTENDANCE_DATA)
3. **Return Response** → Success or duplicate
4. **Dashboard Fetches** → Every 5 seconds via JavaScript

## Performance & Reliability

### Local-First Architecture
- ✅ **Attendance always recorded locally** (CSV file)
- ✅ **Cloud sync is optional** (no blocking)
- ✅ **Works offline** (graceful degradation)

### Timeout & Error Handling
- Connection timeout: 3 seconds
- Automatic fallback if cloud unavailable
- Logs indicate cloud sync status

### Dashboard Updates
- Auto-refresh: 5 seconds
- Real-time statistics
- Paginated attendance table
- CSV export capability

## Dependencies

**Cloud Backend (Ultra-lightweight):**
```
flask
requests
gunicorn
```

**Local System** (add to requirements.txt):
```
requests  # For cloud sync
```

**No heavy AI libraries on cloud!**
- ❌ cv2, mediapipe, face_recognition not needed
- ✅ Cloud is data repository only

## Deployment to Render

### 1. Create `cloud_backend/.env`
```
CLOUD_SYNC_ENABLED=true
```

### 2. Deploy to Render
```bash
cd cloud_backend
git push origin main  # Trigger Render deployment
```

### 3. Update Local Config
```bash
export CLOUD_API_URL="https://ai-attendance-cloud.onrender.com/api/attendance/mark"
```

### 4. Verify
```bash
curl https://ai-attendance-cloud.onrender.com/dashboard
```

## Troubleshooting

### "Cloud service not available"
```
✓ Cloud backend not running?
  → Run: python cloud_backend/app.py

✓ Wrong URL configured?
  → Check: core/cloud_config.py

✓ Firewall blocking?
  → Check port 10000 is accessible
```

### "Duplicate attendance prevented"
```
✓ Same student marked twice today
✓ Cloud returns 200 with status: "duplicate"
✓ Local record is NOT saved again (correct behavior)
```

### Dashboard shows old data
```
✓ Browser cache?
  → Press Ctrl+F5 to refresh

✓ Cloud backend down?
  → Restart: python cloud_backend/app.py

✓ Auto-refresh disabled?
  → Check: dashboard.html (setInterval 5000ms)
```

## Files Modified/Created

```
core/
  ├─ attendance_service.py      (Added cloud sync)
  └─ cloud_config.py             (NEW - config)

cloud_backend/
  ├─ app.py                      (Updated with mark endpoint)
  ├─ static/
  │  └─ style.css                (Professional UI)
  └─ templates/
     └─ dashboard.html           (Real-time dashboard)

test_cloud_sync.py               (NEW - test script)
requirements.txt                 (Added requests)
```

## Summary

✅ **Local system automatically syncs to cloud**
✅ **Professional web dashboard for viewing data**
✅ **Auto-refresh every 5 seconds**
✅ **Works offline (graceful degradation)**
✅ **Ultra-lightweight cloud backend**
✅ **Ready for Render deployment**

The system is production-ready!
