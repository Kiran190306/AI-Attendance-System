#!/usr/bin/env python3
"""
Production Backend Launcher for AI Attendance System
Runs Flask app with production settings
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Production settings
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DEBUG', 'False')

from backend.app import app
from backend.database.db import init_db
import logging

logger = logging.getLogger(__name__)

def main():
    """Start the production server."""
    logger.info("AI Attendance System - Production Backend")

    # Change to the project root directory
    os.chdir(Path(__file__).parent)
    logger.info("Working directory: %s", os.getcwd())

    # Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")

    # Run app
    logger.info("Starting Flask app")
    logger.info("Run with gunicorn: gunicorn backend.app:app --bind 0.0.0.0:$PORT")
    
    # For Render deployment, use:
    # gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app
    
    # For local testing (gunicorn has fcntl issues on Windows):
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

if __name__ == '__main__':
    main()
