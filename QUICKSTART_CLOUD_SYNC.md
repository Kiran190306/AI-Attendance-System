# 🚀 Cloud Sync - Quick Start Guide

## Start Here in 3 Steps

### Step 1️⃣: Start Cloud Backend
```bash
cd cloud_backend
python app.py
```
Server starts on: `http://localhost:10000`

### Step 2️⃣: Local System Auto-Syncs
When your local attendance system marks students, they're automatically sent to cloud:
```python
attendance_service.mark("John Doe", confidence=0.95)
# ↓ Automatically POST to cloud backend
```

### Step 3️⃣: View Dashboard
Open in browser:
```
http://localhost:10000/dashboard
```

**Dashboard updates every 5 seconds automatically!**

---

## What You Get

✅ **Real-time attendance data** from local system
✅ **Professional web dashboard** with live statistics
✅ **Auto-refresh** every 5 seconds
✅ **No heavy dependencies** on cloud
✅ **Works offline** (graceful degradation)
✅ **Ready for Render deployment**

---

## Testing It Works

```bash
# Terminal 1: Start cloud backend
cd cloud_backend && python app.py

# Terminal 2: Test sync (in new terminal)
python test_cloud_sync.py
```

Expected output:
```
✅ Sent 3/3 records successfully

📊 Current attendance data:
   - John Doe at 09:30:00 (confidence: 98.0%)
   - Jane Smith at 09:35:00 (confidence: 95.0%)
   - Alice Johnson at 09:40:00 (confidence: 92.0%)
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/attendance/mark` | Send attendance from local system |
| GET | `/api/attendance` | Get all records (paginated) |
| GET | `/api/attendance/today` | Get today's records only |
| GET | `/api/stats` | Get statistics |
| GET | `/dashboard` | View web dashboard |

---

## Configuration

### Cloud URL (for Render deployment)
Edit `core/cloud_config.py`:
```python
CLOUD_API_URL = "https://your-app.onrender.com/api/attendance/mark"
```

Or set environment variable:
```bash
export CLOUD_API_URL="https://your-app.onrender.com/api/attendance/mark"
```

### Enable/Disable Cloud Sync
```bash
# Enable (default)
export CLOUD_SYNC_ENABLED=true

# Disable (local recording only)
export CLOUD_SYNC_ENABLED=false
```

---

## Files Changed

| File | Change |
|------|--------|
| `core/attendance_service.py` | Added cloud sync function & call |
| `core/cloud_config.py` | NEW - Configuration file |
| `cloud_backend/app.py` | Added POST endpoint, changed port to 10000 |
| `cloud_backend/templates/dashboard.html` | Auto-refresh → 5 seconds |
| `test_cloud_sync.py` | NEW - Test script |
| `requirements.txt` | Added `requests` |

---

## Documentation

📖 **Detailed Guide:** [CLOUD_SYNC_GUIDE.md](CLOUD_SYNC_GUIDE.md)
📖 **Implementation Details:** [CLOUD_SYNC_IMPLEMENTATION.md](CLOUD_SYNC_IMPLEMENTATION.md)

---

## Troubleshooting

**Cloud not syncing?**
```bash
# Check if backend is running
curl http://localhost:10000/api/health

# Test sync manually
python test_cloud_sync.py
```

**Dashboard not updating?**
- Press Ctrl+F5 to clear cache
- Check browser console for errors
- Verify cloud backend is running

**Wrong port?**
- Edit `cloud_backend/app.py` line with `port=10000`

---

## Next: Render Deployment

```bash
# 1. Add your Render URL to config
export CLOUD_API_URL="https://your-render-app.onrender.com/api/attendance/mark"

# 2. Deploy cloud_backend to Render
# 3. Local system automatically syncs

# 4. Access dashboard
# https://your-render-app.onrender.com/dashboard
```

---

## System Is Production Ready! 🎉

- ✅ Local-first architecture
- ✅ Non-blocking cloud sync
- ✅ Professional UI
- ✅ Ultra-lightweight
- ✅ Ready for scale
