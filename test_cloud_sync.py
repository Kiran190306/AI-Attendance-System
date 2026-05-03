#!/usr/bin/env python3
"""
Cloud Sync Demo - Test the attendance data syncing to cloud backend

This script demonstrates how the local attendance system sends data to the cloud.

Setup:
    1. Make sure cloud_backend/app.py is running:
       python cloud_backend/app.py
    
    2. In another terminal, run this script:
       python test_cloud_sync.py
    
    3. Visit the dashboard:
       http://localhost:10000/dashboard
"""

import requests
import json
from datetime import datetime

# Cloud API endpoint (localhost for testing)
CLOUD_API_URL = "http://localhost:10000/api/attendance/mark"

def send_attendance(name, confidence=0.95):
    """Send attendance record to cloud backend."""
    now = datetime.now()
    
    payload = {
        "name": name,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "confidence": confidence,
        "camera_id": "test_camera"
    }
    
    print(f"\n📤 Sending attendance for: {name}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(CLOUD_API_URL, json=payload, timeout=3)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success! Status: {result.get('status')}")
            return True
        else:
            print(f"   ❌ Error! Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error! Is cloud_backend/app.py running?")
        print(f"   Make sure to run: python cloud_backend/app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def get_attendance_data():
    """Fetch attendance data from cloud."""
    try:
        response = requests.get(f"{CLOUD_API_URL.replace('/mark', '')}", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Current attendance data:")
            print(f"   Total records: {data.get('total', 0)}")
            for record in data.get('data', [])[:5]:  # Show first 5
                print(f"   - {record.get('name')} at {record.get('time')} (confidence: {record.get('confidence', 0)*100:.1f}%)")
            return data
        else:
            print(f"❌ Failed to fetch data: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        return None

def main():
    """Run demo."""
    print("=" * 60)
    print("🎓 AI Attendance System - Cloud Sync Demo")
    print("=" * 60)
    
    # Test data
    test_students = [
        ("John Doe", 0.98),
        ("Jane Smith", 0.95),
        ("Alice Johnson", 0.92),
    ]
    
    print("\n1️⃣  Sending test attendance records...")
    success_count = 0
    for name, confidence in test_students:
        if send_attendance(name, confidence):
            success_count += 1
    
    print(f"\n✅ Sent {success_count}/{len(test_students)} records successfully")
    
    # Fetch and display
    print("\n2️⃣  Fetching attendance data from cloud...")
    get_attendance_data()
    
    print("\n3️⃣  Dashboard available at:")
    print("   http://localhost:10000/dashboard")
    
    print("\n" + "=" * 60)
    print("✨ Cloud sync demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
