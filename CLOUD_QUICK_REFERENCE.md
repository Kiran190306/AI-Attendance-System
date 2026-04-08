# Quick Reference: Hybrid Cloud Deployment

## Quick Links

- 📖 [Full Architecture](HYBRID_CLOUD_ARCHITECTURE.md)
- 🚀 [Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)
- 💻 [API Reference](#api-endpoints)
- 📊 [Dashboard](https://your-app.onrender.com/)

## Setup (5 minutes)

### 1. Deploy Cloud Backend
```bash
# Push to GitHub
git add -A && git commit -m "Deploy cloud" && git push

# On Render: Create new Web Service
# - Repository: Your GitHub repo
# - Build: cd cloud_backend && pip install -r requirements.txt
# - Start: cd cloud_backend && gunicorn app:app
```

### 2. Configure Local Machine
```bash
# Edit .env.local
CLOUD_API_URL=https://your-app.onrender.com
CLOUD_SYNC_ENABLED=true
```

### 3. Start Sync
```bash
python example_cloud_sync.py
```

## API Quick Reference

All endpoints return JSON and accept JSON bodies.

### Mark Attendance
```bash
curl -X POST https://your-app.onrender.com/api/attendance/mark \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "confidence": 0.95,
    "camera_id": "camera_1",
    "date": "2024-01-01",
    "time": "10:30:00"
  }'
```

### Get Today's Attendance
```bash
curl https://your-app.onrender.com/api/attendance/today
```

### Get All Records with Pagination
```bash
curl "https://your-app.onrender.com/api/attendance?limit=50&offset=0"
```

### Get Statistics
```bash
curl https://your-app.onrender.com/api/stats
```

### Export Data
```bash
curl https://your-app.onrender.com/api/attendance/export > attendance.json
```

### Health Check
```bash
curl https://your-app.onrender.com/health
```

## Sync Status Checks

### In Python
```python
from sync import get_sync_client

client = get_sync_client()
stats = client.get_stats()

print(f"Pending: {stats['pending_records']}")
print(f"Synced: {stats['total_synced']}")
print(f"Failed: {stats['total_failed']}")
print(f"Healthy: {client.is_healthy()}")
```

### Manual Force Sync
```python
from sync import get_sync_client
get_sync_client().force_sync()
```

## Configuration Files

### .env.local (Local Machine)
```env
CLOUD_API_URL=https://your-cloud.onrender.com
CLOUD_SYNC_ENABLED=true
SYNC_BATCH_SIZE=10
SYNC_INTERVAL_SECONDS=5
SYNC_MAX_RETRIES=5
```

### cloud_backend/.env (Cloud Server)
```env
FLASK_ENV=production
FLASK_DEBUG=false
```

## Directory Structure

```
Root/
├── sync/                          ← Sync module
│   ├── __init__.py
│   └── sync_client.py
├── cloud_backend/                 ← Cloud application
│   ├── app.py
│   ├── routes/
│   ├── templates/
│   ├── Procfile
│   ├── requirements.txt
│   └── data/
├── .env.local                     ← Local config
├── example_cloud_sync.py          ← Example script
└── README.md
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Sync not working | Check `CLOUD_API_URL` in `.env.local` |
| Cloud returns 502 | Restart service in Render dashboard |
| Dashboard shows no data | Mark attendance and wait 5-10 seconds |
| Records queued but not synced | Check internet connection, verify cloud URL |
| Import error for sync module | Install requests: `pip install requests` |

## File Locations

- **Local data**: `attendance/attendance.csv`
- **Sync queue**: `.sync_queue.json` (persisted local queue)
- **Cloud data**: `cloud_backend/data/attendance.json`
- **Config**: `.env.local` and `cloud_backend/.env`

## Monitoring

### Check Local Sync Status
```python
from core.attendance_service_cloud import AttendanceServiceWithCloudSync

att = AttendanceServiceWithCloudSync()
status = att.get_sync_status()
print(status)
```

### Check Cloud Health
```bash
curl https://your-app.onrender.com/health
```

### View Cloud Logs
- Go to Render dashboard
- Select your service
- Click "Logs"

## Common Commands

```bash
# Mark attendance example
python example_cloud_sync.py

# Check sync status
python -c "from sync import get_sync_client; print(get_sync_client().get_stats())"

# Force sync
python -c "from sync import get_sync_client; get_sync_client().force_sync()"

# View local attendance
cat attendance/attendance.csv

# Restart cloud service (on Render)
# Click "Restart Web Service" in dashboard
```

## Performance Tips

1. **Increase sync interval** if API is slow (more delay, fewer requests)
   ```env
   SYNC_INTERVAL_SECONDS=10
   ```

2. **Increase batch size** for fewer API calls
   ```env
   SYNC_BATCH_SIZE=25
   ```

3. **Reduce retries** for faster failure handling
   ```env
   SYNC_MAX_RETRIES=2
   ```

## Security Checklist

- [ ] Cloud URL is accessible
- [ ] .env files are in .gitignore
- [ ] No credentials in code
- [ ] Cloud backend is not public (for sensitive deployments)
- [ ] Regular backups of attendance.csv
- [ ] Check sync logs periodically

## Support & Further Help

- Architecture Details: [HYBRID_CLOUD_ARCHITECTURE.md](HYBRID_CLOUD_ARCHITECTURE.md)
- Deployment Steps: [CLOUD_DEPLOYMENT_GUIDE.md](CLOUD_DEPLOYMENT_GUIDE.md)
- Main README: [README.md](README.md)

## Example Integration Code

```python
# Complete working example
from core.attendance_service_cloud import AttendanceServiceWithCloudSync
from sync import init_sync_client
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

# Start sync
sync = init_sync_client(os.getenv('CLOUD_API_URL'))
sync.start_sync()

# Mark attendance
att = AttendanceServiceWithCloudSync(enable_cloud_sync=True)
att.mark('John Doe', confidence=0.95, camera_id='cam1')

# Check status
print(att.get_session_stats())
print(sync.get_stats())
```

---
**Last Updated**: 2024
**Version**: 1.0
