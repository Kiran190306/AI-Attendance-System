# Hybrid Cloud Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Deployment Architecture](#deployment-architecture)
3. [Step-by-Step Cloud Deployment](#step-by-step-cloud-deployment)
4. [Local System Configuration](#local-system-configuration)
5. [Verification & Testing](#verification--testing)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

## Prerequisites

### Requirements
- GitHub account (for version control)
- Render.com account (free tier available)
- Local development environment with Python 3.10+
- Git installed on local machine

### Accounts Setup
1. **GitHub**: https://github.com/signup
2. **Render**: https://render.com/ (Sign up with GitHub for easier integration)

## Deployment Architecture

```
Your Local Attendance System (Camera + AI)
                ↓
        Mark Attendance Locally
                ↓
        Queue to Cloud via API
                ↓
    Render Cloud Backend (Flask)
                ↓
        Store in attendance.json
                ↓
     Dashboard (HTML + JavaScript)
                ↓
    Accessible via public URL
```

## Step-by-Step Cloud Deployment

### Step 1: Prepare Cloud Backend Code

The cloud backend is located in `cloud_backend/` directory with the following structure:

```
cloud_backend/
├── app.py                 # Main Flask application
├── routes/
│   ├── __init__.py
│   └── attendance_routes.py    # API endpoints
├── templates/
│   └── dashboard.html     # Web dashboard
├── Procfile              # Deployment configuration
├── requirements.txt      # Python dependencies
└── data/                 # Data storage directory
```

### Step 2: Push Code to GitHub

1. **Initialize or update git repository:**
```bash
cd d:\AI-Attendance-System
git init
git add -A
git commit -m "Add hybrid cloud deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/AI-Attendance-System.git
git push -u origin main
```

2. **Verify on GitHub**: Visit your repository and confirm files are uploaded

### Step 3: Deploy on Render

#### Option A: Using Render Dashboard (Recommended)

1. **Go to Render.com**
   - Login with your GitHub account
   - Click "New +" → "Web Service"

2. **Connect GitHub Repository**
   - Select "Build and deploy from a Git repository"
   - Click "Connect GitHub"
   - Authorize Render to access your repositories
   - Select your `AI-Attendance-System` repository
   - Click "Connect"

3. **Configure Web Service**
   - **Name**: `ai-attendance-cloud` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r cloud_backend/requirements.txt`
   - **Start Command**: `cd cloud_backend && gunicorn -w 4 -b 0.0.0.0:$PORT app:app`

4. **Set Environment Variables**
   - Click "Environment"
   - Add these variables:
     ```
     FLASK_ENV=production
     FLASK_DEBUG=false
     ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (2-3 minutes)
   - You'll get a URL like: `https://ai-attendance-cloud.onrender.com`

#### Option B: Using Render CLI

If you prefer command line:

```bash
# Install Render CLI
npm install -g @render-com/cli

# Login
render login

# Create service from root
render create --repo YOUR_GITHUB_URL
```

### Step 4: Verify Cloud Deployment

1. **Test Health Endpoint**
```bash
curl https://ai-attendance-cloud.onrender.com/health
```

Expected response:
```json
{
  "status": "OK",
  "timestamp": "2024-01-01T10:30:00.123456",
  "service": "AI Attendance System - Cloud Backend"
}
```

2. **Test Dashboard**
   - Open in browser: `https://ai-attendance-cloud.onrender.com/`
   - You should see the attendance dashboard

3. **Test API Endpoints**
```bash
# Get today's attendance
curl https://ai-attendance-cloud.onrender.com/api/attendance/today

# Get all records
curl https://ai-attendance-cloud.onrender.com/api/attendance

# Get statistics
curl https://ai-attendance-cloud.onrender.com/api/stats
```

## Local System Configuration

### Step 1: Install Sync Module Dependencies

```bash
cd d:\AI-Attendance-System

# Install requests library (needed for sync)
pip install requests

# Or install from updated requirements.txt
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create or update `.env.local` file in the root directory:

```env
CLOUD_API_URL=https://your-cloud-service.onrender.com
CLOUD_SYNC_ENABLED=true
SYNC_BATCH_SIZE=10
SYNC_INTERVAL_SECONDS=5
SYNC_MAX_RETRIES=5
```

Replace `your-cloud-service` with your actual Render app URL (found in Render dashboard).

### Step 3: Initialize Sync Client

Add this to your main attendance script or `run_system.py`:

```python
import os
from dotenv import load_dotenv
from sync import init_sync_client

# Load environment variables
load_dotenv('.env.local')

# Initialize sync client
cloud_url = os.getenv('CLOUD_API_URL')
sync_enabled = os.getenv('CLOUD_SYNC_ENABLED', 'true').lower() == 'true'

if sync_enabled and cloud_url:
    sync_client = init_sync_client(
        cloud_url=cloud_url,
        batch_size=int(os.getenv('SYNC_BATCH_SIZE', 10)),
        sync_interval=float(os.getenv('SYNC_INTERVAL_SECONDS', 5)),
        max_retries=int(os.getenv('SYNC_MAX_RETRIES', 5))
    )
    sync_client.start_sync()
    print(f"✓ Cloud sync enabled: {cloud_url}")
else:
    print("ℹ Cloud sync disabled")
```

### Step 4: Update Attendance Marking

Use the cloud-enabled attendance service:

```python
from core.attendance_service_cloud import AttendanceServiceWithCloudSync

# Initialize with cloud sync
attendance = AttendanceServiceWithCloudSync(
    csv_path='attendance/attendance.csv',
    enable_cloud_sync=True
)

# Mark attendance (automatically syncs to cloud)
attendance.mark(
    student_name='John Doe',
    confidence=0.95,
    camera_id='camera_1'
)

# Check sync status
sync_status = attendance.get_sync_status()
print(f"Sync healthy: {sync_status['is_healthy']}")
```

## Verification & Testing

### Local Testing

1. **Test Local Attendance Marking**
```python
python -c "
from core.attendance_service_cloud import AttendanceServiceWithCloudSync
from sync import init_sync_client

# Initialize sync
sync_client = init_sync_client('http://localhost:5000')

# Initialize attendance
att = AttendanceServiceWithCloudSync(enable_cloud_sync=True)

# Mark attendance
result = att.mark('Test Student', confidence=0.98, camera_id='test_cam')
print(f'Marked: {result}')

# Check queue
sync_client.force_sync()
"
```

2. **Test Cloud Connection**
```python
import requests

cloud_url = 'https://your-cloud-service.onrender.com'

# Test health
response = requests.get(f'{cloud_url}/health')
print(f"Cloud Health: {response.json()}")

# Test mark endpoint
response = requests.post(
    f'{cloud_url}/api/attendance/mark',
    json={
        'name': 'Test User',
        'confidence': 0.95,
        'camera_id': 'test',
        'date': '2024-01-01',
        'time': '10:30:00',
        'timestamp_iso': '2024-01-01T10:30:00'
    }
)
print(f"Mark Response: {response.json()}")
```

### End-to-End Testing

1. **Mark Attendance Locally**
   - Run your face recognition system
   - Let it mark a student's attendance
   - Check local `attendance/attendance.csv`

2. **Verify Cloud Sync**
   - Wait 5-10 seconds (sync interval)
   - Open cloud dashboard: `https://your-cloud-service.onrender.com`
   - Should see the marked attendance

3. **Check API Directly**
```bash
curl https://your-cloud-service.onrender.com/api/attendance/today
```

Should show the recently marked attendance.

## Troubleshooting

### Cloud Deployment Issues

**Problem**: Deployment fails on Render
- **Solution**: Check build logs in Render dashboard
  - Verify `requirements.txt` is in `cloud_backend/` directory
  - Ensure Python version is 3.8+
  - Check for syntax errors in `app.py`

**Problem**: 502 Bad Gateway Error
- **Solution**:
  1. Check app logs: Render Dashboard → Logs
  2. Restart the service: Render Dashboard → Settings → Restart Web Service
  3. Verify Flask app starts without errors locally first

**Problem**: Dashboard shows "Cannot connect to Cloud"
- **Solution**:
  1. Verify the cloud URL in browser (should show health endpoint)
  2. Check CORS configuration in `app.py` (should have `CORS(app)`)
  3. Review browser console for network errors

### Sync Issues

**Problem**: Records not appearing in cloud dashboard
- **Solution**:
  1. Verify `CLOUD_API_URL` is correct in `.env.local`
  2. Check cloud backend is running: `curl https://your-url/health`
  3. Check local sync logs (enable debug logging)
  4. Try manual sync: `python -c "from sync import get_sync_client; get_sync_client().force_sync()"`

**Problem**: High pending_records count
- **Solution**:
  1. Increase `SYNC_INTERVAL_SECONDS` to sync less frequently
  2. Decrease `SYNC_BATCH_SIZE` if API is timing out
  3. Check cloud backend response times
  4. Increase `SYNC_MAX_RETRIES` for flaky networks

**Problem**: Sync stops working after restart
- **Solution**:
  1. Verify sync client is initialized in your main script
  2. Check `.sync_queue.json` file exists for persistence
  3. Restart the local application

### Local Network Issues

**Problem**: "Connection refused" when connecting to local Flask
- **Solution**: This is expected when not testing locally. Only test against deployed cloud URL.

**Problem**: Timeout errors during sync
- **Solution**:
  1. Check internet connection
  2. Increase timeout in configuration
  3. Check if cloud service is sleeping (Render free tier sleeps after 15 min inactivity)

## Maintenance

### Monitoring

1. **Check Cloud Service Status**
   - Render Dashboard → Your Service → Logs
   - Look for errors or warnings

2. **Monitor Disk Usage**
   - Render free tier has limited storage
   - Monitor `cloud_backend/data/attendance.json` size
   - Archive old data if needed

3. **Check Sync Health**
```python
from sync import get_sync_client

client = get_sync_client()
stats = client.get_stats()
print(f"Pending records: {stats['pending_records']}")
print(f"Success rate: {stats['total_synced'] / (stats['total_synced'] + stats['total_failed']):.1%}")
```

### Database Migration (Optional)

To upgrade from JSON to database:

1. **Backup JSON data**
```bash
cp cloud_backend/data/attendance.json cloud_backend/data/attendance_backup.json
```

2. **Add database support** to `cloud_backend/app.py`:
```python
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)
```

3. **Migrate data** from JSON to database

4. **Update routes** to use database instead of JSON

### Data Backup

1. **Regular backups** of `cloud_backend/data/attendance.json`
2. **Export data** via API: `/api/attendance/export`
3. **Keep local CSV** as primary backup

### Scaling to Production

To run in production:

1. **Use proper database** (PostgreSQL recommended)
2. **Add authentication** (JWT or API keys)
3. **Enable HTTPS** and SSL certificates
4. **Add rate limiting** to prevent abuse
5. **Implement caching** (Redis)
6. **Use CDN** for static files
7. **Set up monitoring** (error tracking, performance)
8. **Enable backups** and disaster recovery

## Advanced Configuration

### Custom Domain (Future)

When ready to use a custom domain:

1. Buy domain from registrar (GoDaddy, Namecheap, etc.)
2. Add DNS records pointing to Render
3. Enable custom domain in Render settings
4. Update `CLOUD_API_URL` in `.env.local`

### Environment-Specific Config

Use different `.env` files for different environments:

```bash
# Development (local testing)
CLOUD_API_URL=http://localhost:5000
CLOUD_SYNC_ENABLED=false

# Production (on render)
CLOUD_API_URL=https://ai-attendance-cloud.onrender.com
CLOUD_SYNC_ENABLED=true
```

### Performance Tuning

If experiencing slow syncs:

1. Increase `SYNC_BATCH_SIZE` to 25-50 (if cloud supports it)
2. Increase `SYNC_INTERVAL_SECONDS` to 10-30
3. Add caching headers to cloud responses
4. Compress JSON payloads

## Summary

You now have a complete hybrid cloud deployment where:
- ✓ Local system runs face recognition (fast, private)
- ✓ Cloud backend centrally stores all attendance data
- ✓ Sync happens automatically in background
- ✓ Public dashboard accessible anywhere
- ✓ Works even without internet (offline-first)
- ✓ Scales to multiple locations

**Next**: Monitor your deployment and plan for production features like authentication, database, and backups.
