"""
Cloud Backend Configuration

Configure the cloud API endpoint for syncing attendance data.
This allows the local attendance system to automatically upload
records to a remote cloud server.

Usage:
    1. For local development:
       - Leave CLOUD_API_URL as default (localhost:10000)
       - Run local Flask app with: python cloud_backend/app.py
    
    2. For Render deployment:
       - Update CLOUD_API_URL to your Render URL
       - Example: https://ai-attendance-cloud.onrender.com/api/attendance/mark
       - Set via environment variable: CLOUD_API_URL=<your-url>
    
    3. Or update this file directly:
"""

import os

# Local development (default)
CLOUD_API_URL = os.environ.get(
    "CLOUD_API_URL",
    "http://localhost:10000/api/attendance/mark"
)

# Render production example:
# CLOUD_API_URL = "https://your-app.onrender.com/api/attendance/mark"

# Cloud sync timeout (seconds)
CLOUD_SYNC_TIMEOUT = 3

# Enable/disable cloud sync
CLOUD_SYNC_ENABLED = os.environ.get("CLOUD_SYNC_ENABLED", "true").lower() == "true"

# Cloud API key (optional for future authentication)
CLOUD_API_KEY = os.environ.get("CLOUD_API_KEY", "")

__all__ = ["CLOUD_API_URL", "CLOUD_SYNC_TIMEOUT", "CLOUD_SYNC_ENABLED", "CLOUD_API_KEY"]
