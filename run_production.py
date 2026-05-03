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

def main():
    """Start the production server."""
    print("=" * 70)
    print("AI Attendance System - Production Backend")
    print("=" * 70)
    
    # Initialize database
    print("✓ Initializing database...")
    init_db()
    print("✓ Database initialized")
    
    # Run app
    print("✓ Starting Flask app...")
    print(f"✓ Running on http://0.0.0.0:$PORT")
    print("=" * 70)
    
    # For Render deployment, use:
    # gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app
    
    # For local testing:
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

if __name__ == '__main__':
    main()
