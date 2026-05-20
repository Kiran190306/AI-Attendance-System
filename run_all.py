#!/usr/bin/env python3
"""
Complete AI Attendance System Runner
Sets up and runs the entire system
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return success."""
    print(f"✓ {description}")
    try:
        if sys.platform == "win32":
            # On Windows, use shell=True and handle activation differently
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        print(f"Output: {e.output}")
        return False

def main():
    print("=" * 60)
    print("AI Attendance System - Complete Setup & Run")
    print("=" * 60)

    project_root = Path(__file__).parent

    # Change to project directory
    os.chdir(project_root)
    print(f"✓ Working directory: {os.getcwd()}")

    # Create virtual environment if needed
    if not Path("venv").exists():
        print("✓ Creating virtual environment...")
        if not run_command("python -m venv venv", "Virtual environment created"):
            return 1

    # Activate virtual environment
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate.bat"
    else:
        activate_cmd = "source venv/bin/activate"

    # Install dependencies
    print("✓ Installing dependencies...")
    pip_cmd = "pip install -r requirements.txt"
    if not run_command(pip_cmd, "Dependencies installed"):
        return 1

    # Initialize database
    print("✓ Initializing database...")
    db_cmd = "python -c \"from backend.database.db import init_db; init_db()\""
    if not run_command(db_cmd, "Database initialized"):
        return 1

    # Start backend server
    print("✓ Starting backend server...")
    backend_cmd = "python run_production.py"
    backend_process = subprocess.Popen(backend_cmd, shell=True)
    print(f"✓ Backend started (PID: {backend_process.pid})")

    # Wait for server to start
    print("✓ Waiting for server to start...")
    time.sleep(5)

    # Test API
    print("✓ Testing API...")
    try:
        import requests
        response = requests.get('http://localhost:5000/api/test', timeout=5)
        if response.status_code == 200 and response.json().get('status') == 'ok':
            print("✓ API test passed")
        else:
            print("✗ API test failed")
            return 1
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return 1

    # Open browser
    print("✓ Opening browser...")
    webbrowser.open('http://localhost:5000')

    print("=" * 60)
    print("🎉 System is running!")
    print("📱 Frontend: http://localhost:5000")
    print("🔧 Backend API: http://localhost:5000/api/test")
    print("📊 Attendance API: http://localhost:5000/api/attendance")
    print("=" * 60)
    print("To run face recognition: python attendance_system.py")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n✓ Shutting down...")
        backend_process.terminate()
        backend_process.wait()

    return 0

if __name__ == "__main__":
    sys.exit(main())