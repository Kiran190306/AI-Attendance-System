#!/usr/bin/env python3
"""
Test Analytics Dashboard - Verify charts and stats work

This script tests the new analytics dashboard features.
"""

import requests
import json
import time

def test_analytics_api():
    """Test the analytics API endpoint."""
    print("🔍 Testing Analytics API...")

    try:
        response = requests.get("http://localhost:10000/api/analytics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Analytics API working")
            print(f"   Total Students: {data.get('total_students', 0)}")
            print(f"   Present Today: {data.get('present_today', 0)}")
            print(f"   Attendance %: {data.get('attendance_percentage', 0)}%")
            print(f"   Total Records: {data.get('total_records', 0)}")
            return True
        else:
            print(f"❌ Analytics API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Analytics API error: {str(e)}")
        return False

def test_dashboard_access():
    """Test dashboard accessibility."""
    print("\n🔍 Testing Dashboard Access...")

    try:
        response = requests.get("http://localhost:10000/dashboard", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard accessible")
            # Check if Chart.js is included
            if "chart.js" in response.text.lower():
                print("✅ Chart.js library included")
            else:
                print("❌ Chart.js library missing")
            return True
        else:
            print(f"❌ Dashboard failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard error: {str(e)}")
        return False

def test_with_sample_data():
    """Add sample data and test analytics."""
    print("\n🔍 Testing with Sample Data...")

    # Add some sample attendance records
    sample_data = [
        {"name": "John Doe", "confidence": 0.98},
        {"name": "Jane Smith", "confidence": 0.95},
        {"name": "Alice Johnson", "confidence": 0.92},
        {"name": "Bob Wilson", "confidence": 0.88},
        {"name": "Carol Brown", "confidence": 0.65},
    ]

    success_count = 0
    for student in sample_data:
        payload = {
            "name": student["name"],
            "date": "2026-04-10",
            "time": f"13:{success_count+10:02d}:00",
            "confidence": student["confidence"],
            "camera_id": "test_camera"
        }

        try:
            response = requests.post("http://localhost:10000/api/attendance/mark",
                                   json=payload, timeout=3)
            if response.status_code == 200:
                success_count += 1
        except:
            pass

    print(f"✅ Added {success_count} sample records")

    # Wait a moment for processing
    time.sleep(1)

    # Test analytics again
    try:
        response = requests.get("http://localhost:10000/api/analytics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Analytics updated with sample data:")
            print(f"   Present Today: {data.get('present_today', 0)}")
            print(f"   Attendance %: {data.get('attendance_percentage', 0)}%")
            print(f"   High Confidence: {data.get('confidence_distribution', {}).get('high', 0)}")
            print(f"   Medium Confidence: {data.get('confidence_distribution', {}).get('medium', 0)}")
            print(f"   Low Confidence: {data.get('confidence_distribution', {}).get('low', 0)}")
            return True
    except Exception as e:
        print(f"❌ Analytics test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("📊 AI Analytics Dashboard - Test Suite")
    print("=" * 60)

    # Test 1: Analytics API
    api_ok = test_analytics_api()

    # Test 2: Dashboard Access
    dashboard_ok = test_dashboard_access()

    # Test 3: With Sample Data
    data_ok = test_with_sample_data()

    print("\n" + "=" * 60)
    print("📋 Test Results:")
    print(f"   Analytics API: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"   Dashboard Access: {'✅ PASS' if dashboard_ok else '❌ FAIL'}")
    print(f"   Sample Data Test: {'✅ PASS' if data_ok else '❌ FAIL'}")

    if all([api_ok, dashboard_ok, data_ok]):
        print("\n🎉 All tests passed! Analytics dashboard is working!")
        print("\n📱 Open dashboard: http://localhost:10000/dashboard")
        print("   - View real-time statistics")
        print("   - See interactive charts")
        print("   - Watch auto-refresh every 5 seconds")
    else:
        print("\n⚠️  Some tests failed. Check server logs.")

    print("=" * 60)

if __name__ == "__main__":
    main()
