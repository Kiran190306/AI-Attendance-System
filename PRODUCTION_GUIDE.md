# Production System Integration Guide

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 MOBILE APP (Android)                    │
│  - LoginActivity: User authentication                   │
│  - DashboardActivity: Analytics visualization          │
│  - AttendanceActivity: Records display                 │
│  - Retrofit: HTTP client with token handling           │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTPS (Bearer Token)
                     ▼
┌─────────────────────────────────────────────────────────┐
│              BACKEND API (Flask + SQLite)               │
│  - /api/login: JWT token generation                    │
│  - /api/signup: User registration                      │
│  - /api/attendance: Get attendance records             │
│  - /api/analytics: Get analytics data                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            DATABASE (SQLite)                            │
│  - users: Credentials and user metadata                |
│  - attendance_logs: Attendance records                 |
│  - students: Student information                       |
└─────────────────────────────────────────────────────────┘
```

## Part 1: Backend Production Deployment

### Step 1: Prepare Backend for Render

#### 1.1 Update Backend Configuration

File: `backend/config.py`

```python
import os

# Production settings
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# In production, generate strong SECRET_KEY
if not os.environ.get('SECRET_KEY'):
    import secrets
    SECRET_KEY = secrets.token_urlsafe(32)
```

#### 1.2 Create Procfile for Render

File: `Procfile`

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app
```

#### 1.3 Update requirements.txt

```
Flask>=2.3,<3
Flask-Cors>=3.0
SQLAlchemy>=2.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
Pillow>=10.2.0
gunicorn>=21.0.0
python-dotenv>=1.0
```

#### 1.4 Create .env.example (for reference)

```
DEBUG=False
SECRET_KEY=your-secret-key-here-min-32-chars
DATABASE_URL=sqlite:///attendance.db
```

### Step 2: Deploy to Render

1. **Create GitHub Repository:**
```bash
cd d:\AI-Attendance-System
git init
git add .
git commit -m "Initial production release"
git branch -M main
git remote add origin https://github.com/your-username/ai-attendance.git
git push -u origin main
```

2. **Deploy on Render:**
   - Visit https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - Name: `ai-attendance-backend`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app`
   - Add Environment Variables:
     - `SECRET_KEY`: (generate random 32+ character string)
     - `DEBUG`: `False`
     - `PYTHON_VERSION`: `3.10`
   - Click "Create Web Service"

3. **Test Deployment:**
   - Wait for build to complete
   - Get your URL (e.g., `https://ai-attendance-backend.onrender.com`)
   - Test: `curl https://ai-attendance-backend.onrender.com/api/system/status`

### Step 3: Create Initial User (for testing)

```bash
# SSH into Render or use local test
python -c "
from backend.services.user_service import create_user
user = create_user('demo', 'demo@example.com', 'password123')
print(f'Created user: {user.username}')
"
```

---

## Part 2: Android App Setup & Build

### Step 1: Update API Configuration

File: `android_app/app/src/main/java/com/attendance/app/api/RetrofitClient.java`

```java
public class RetrofitClient {
    private static final String BASE_URL = "https://your-render-url.onrender.com";
    // Update this to your actual Render deployment URL
}
```

### Step 2: Build Debug APK (Testing)

```bash
cd android_app

# Build debug APK
./gradlew assembleDebug

# Output: app/build/outputs/apk/debug/app-debug.apk
```

### Step 3: Install on Android Device/Emulator

**Using ADB:**
```bash
# Connect device via USB or start emulator
adb install app/build/outputs/apk/debug/app-debug.apk

# Or run directly from Android Studio
# Device → Right-click → Run
```

**Using Android Studio:**
- Open Android Studio
- Open `android_app` folder
- Click "Run" (green play button)
- Select target device/emulator

### Step 4: Test App

1. **Login Screen:**
   - Username: `demo`
   - Password: `password123`
   - Click Login

2. **Dashboard:**
   - View analytics cards
   - Pull down to refresh
   - Click "View Attendance"

3. **Attendance Screen:**
   - See all attendance records
   - Pull down to refresh

### Step 5: Build Release APK

```bash
cd android_app

# Build release APK (signing required)
./gradlew assembleRelease

# Output: app/build/outputs/apk/release/app-release.apk
```

---

## Part 3: Complete API Reference

### Authentication Endpoints

#### POST /api/login
**Request:**
```json
{
  "username": "demo",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "demo",
    "email": "demo@example.com"
  }
}
```

#### POST /api/signup
**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepass123"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "username": "newuser",
    "email": "user@example.com"
  }
}
```

### Protected Endpoints

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

#### GET /api/attendance
**Response (200 OK):**
```json
[
  {
    "student_name": "John Doe",
    "date": "2024-04-10",
    "timestamp": "2024-04-10T09:30:00",
    "confidence": 0.95
  }
]
```

#### GET /api/analytics
**Response (200 OK):**
```json
{
  "total_students": 50,
  "present_today": 48,
  "late_students": 3,
  "attendance_percentage": 96.0,
  "total_records": 2400,
  "weekly_unique_attendees": 47
}
```

---

## Part 4: Testing & Validation

### Backend Testing

```bash
# Test with curl
BASE_URL="https://your-render-url.onrender.com"

# 1. Login
curl -X POST $BASE_URL/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"password123"}'

# 2. Use token from response
TOKEN="your-token-here"

# 3. Get analytics
curl -X GET $BASE_URL/api/analytics \
  -H "Authorization: Bearer $TOKEN"

# 4. Get attendance
curl -X GET $BASE_URL/api/attendance \
  -H "Authorization: Bearer $TOKEN"
```

### Android Testing Checklist

- [ ] App launches successfully
- [ ] Can login with valid credentials
- [ ] Login fails with invalid credentials
- [ ] Dashboard loads analytics data
- [ ] Pull-to-refresh works
- [ ] View Attendance shows records
- [ ] Can logout
- [ ] Network error handling works
- [ ] App doesn't crash on network issues
- [ ] Token persists after restart
- [ ] Token cleared after logout

---

## Part 5: Production Deployment Checklist

### Backend
- [ ] Deployed to Render
- [ ] Environment variables set
- [ ] Database initialized
- [ ] Test /api/login endpoint
- [ ] Test /api/analytics endpoint
- [ ] HTTPS working
- [ ] Error logging enabled
- [ ] Render URL copied

### Android
- [ ] API endpoint configured
- [ ] Debug APK builds
- [ ] Tested on emulator
- [ ] Tested on physical device
- [ ] Release APK builds
- [ ] ProGuard configured
- [ ] Signed APK ready
- [ ] Ready for Play Store

---

## Part 6: Running Locally (Development)

### Backend

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
set FLASK_ENV=development
set DEBUG=True
set SECRET_KEY=dev-key

# Run
python run_production.py
# Server runs on http://localhost:5000
```

### Android

```bash
cd android_app

# For local testing, update RetrofitClient.java:
# private static final String BASE_URL = "http://10.0.2.2:5000";
# (10.0.2.2 is how emulator accesses localhost)

./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

---

## Part 7: Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Attendance Logs Table
```sql
CREATE TABLE attendance_logs (
    id INTEGER PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT NOT NULL,
    UNIQUE(student_name, date)
);
```

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Success Indicators

✅ **Backend Ready:**
- API responds to requests
- Authentication working
- Token validation passing
- Database working

✅ **Android Ready:**
- App installs without errors
- Native feel and performance
- Smooth animations
- Quick load times

✅ **Integration Ready:**
- App connects to backend
- Login/logout works
- Data displays correctly
- Refresh functionality works

---

## Next Steps

1. Deploy backend to Render
2. Get Render URL
3. Update Android app with URL
4. Build and test APK
5. Submit to Google Play Store (optional)
6. Monitor performance
7. Regular updates based on feedback
