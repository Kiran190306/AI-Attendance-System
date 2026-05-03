"""
Quick Start Guide for AI Attendance System Production

This guide provides step-by-step instructions to deploy the system.
"""

import os
import sys

print("""
╔════════════════════════════════════════════════════════════════════╗
║    AI ATTENDANCE SYSTEM - PRODUCTION QUICK START                  ║
╚════════════════════════════════════════════════════════════════════╝

OPTION 1: Deploy Backend on Render
──────────────────────────────────

1. Push code to GitHub
   $ git push origin main

2. Go to https://dashboard.render.com

3. Create new Web Service:
   - GitHub repo: your-ai-attendance-repo
   - Build: pip install -r backend/requirements.txt
   - Start: gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app
   - Env vars:
     * SECRET_KEY=<random-32-char-string>
     * DEBUG=False

4. Get URL (e.g., https://ai-attendance.onrender.com)

5. Update Android: RetrofitClient.java
   BASE_URL = "https://ai-attendance.onrender.com"


OPTION 2: Build Android App
─────────────────────────────

1. Configure Android app:
   cd android_app/app/src/main/java/com/attendance/app/api/
   Update: RetrofitClient.java → BASE_URL

2. Build:
   cd android_app
   ./gradlew assembleDebug

3. Install:
   adb install app/build/outputs/apk/debug/app-debug.apk

4. Test:
   - Login with demo/password123
   - View dashboard and attendance


OPTION 3: Local Testing
──────────────────────

Backend:
  $ pip install -r backend/requirements.txt
  $ python run_production.py

Android (local testing):
  1. Update RetrofitClient.java:
     BASE_URL = "http://10.0.2.2:5000"
  2. Run emulator
  3. Build and run app


FILES STRUCTURE
────────────────

Backend:
  ✓ backend/app.py - Main Flask app
  ✓ backend/api/routes_auth.py - Login/signup
  ✓ backend/api/routes_attendance.py - Attendance API
  ✓ backend/api/routes_analytics.py - Analytics API
  ✓ backend/services/user_service.py - Auth logic
  ✓ backend/database/models.py - Database models
  ✓ Procfile - Render configuration

Android:
  ✓ android_app/app/src/main/java/com/attendance/app/
    ├── api/ - Retrofit client & models
    ├── ui/
    │   ├── login/LoginActivity.java
    │   ├── dashboard/DashboardActivity.java
    │   └── attendance/AttendanceActivity.java
    └── utils/
        ├── TokenManager.java
        └── NetworkUtil.java
  ✓ android_app/app/src/main/res/
    ├── layout/ - XML layouts
    ├── values/ - Strings & colors
    └── ...


API ENDPOINTS
─────────────

POST /api/login
  Request: {"username":"demo", "password":"password123"}
  Response: {"access_token":"...", "user":{...}}

POST /api/signup
  Request: {"username":"user", "email":"user@example.com", "password":"pass"}
  Response: {"access_token":"...", "user":{...}}

GET /api/attendance
  Header: Authorization: Bearer <token>
  Response: [{"student_name":"...", "date":"...", ...}]

GET /api/analytics
  Header: Authorization: Bearer <token>
  Response: {"total_students":50, "present_today":48, ...}


TROUBLESHOOTING
───────────────

Backend won't start:
  $ pip install -r backend/requirements.txt
  $ python -c "from backend.app import app; print('OK')"

Android won't connect:
  - Check BASE_URL in RetrofitClient.java
  - Emulator: use 10.0.2.2 for localhost
  - Device: use actual IP address
  - Check network connectivity

Build errors:
  $ cd android_app
  $ ./gradlew clean
  $ ./gradlew assembleDebug


DEMO CREDENTIALS
─────────────────

Username: demo
Password: password123

(Create new users via signup)


NEXT STEPS
──────────

1. ✓ Backend deployed
2. ✓ Android app built
3. ✓ Test login/logout
4. ✓ Test attendance view
5. ✓ Test analytics display
6. → Optional: Submit to Google Play Store


DOCUMENTATION
──────────────

Detailed guide: PRODUCTION_GUIDE.md
Build instructions: android_app/BUILD_INSTRUCTIONS.md
""")
