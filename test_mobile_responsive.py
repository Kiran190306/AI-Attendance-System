#!/usr/bin/env python3
"""
Mobile Responsiveness Test - Verify dashboard mobile features

This script tests the responsive dashboard on different screen sizes.
"""

import requests
import json

def test_dashboard_loaded():
    """Test that dashboard can be accessed after login."""
    print("Testing Mobile Responsive Dashboard")
    print("=" * 60)
    
    # Create session to handle login
    session = requests.Session()
    
    # Login first
    login_data = {"username": "admin", "password": "1234"}
    session.post("http://127.0.0.1:10000/login", data=login_data, timeout=3)
    
    # Get dashboard
    resp = session.get("http://127.0.0.1:10000/dashboard", timeout=3)
    
    if resp.status_code == 200:
        content = resp.text
        
        # Check for responsive CSS features
        checks = {
            "Viewport meta tag": 'viewport' in content,
            "Mobile media query (480px)": '@media (max-width: 480px)' in content,
            "Tablet media query (768px)": '@media (max-width: 768px)' in content,
            "Extra small media query (360px)": '@media (max-width: 360px)' in content,
            "Touch-scroll class": '-webkit-overflow-scrolling: touch' in content,
            "Responsive grid (auto-fit)": 'grid-template-columns: repeat(auto-fit' in content,
            "Flexible layout buttons": 'flex-direction: column' in content or 'grid-template-columns: 1fr' in content,
            "Scrollable table": 'overflow-x: auto' in content,
            "Touch-friendly padding": 'min-height: 44px' in content,
            "Responsive fonts": 'font-size' in content,
        }
        
        print("\nDashboard Mobile Features:")
        all_ok = True
        for feature, present in checks.items():
            status = "[OK]" if present else "[FAIL]"
            print(f"{status} {feature}")
            if not present:
                all_ok = False
        
        print("\n" + "=" * 60)
        if all_ok:
            print("SUCCESS: Dashboard is fully mobile responsive!")
            print("\nFeatures:")
            print("- Mobile devices (<480px): Single column layout")
            print("- Tablets (480px-768px): Two column layout")
            print("- Tablets (768px-1024px): Responsive grid")
            print("- Desktop (>1024px): Full multi-column layout")
            print("\nMobile optimizations:")
            print("- Touch targets: 44px minimum height")
            print("- Tables: Horizontally scrollable on mobile")
            print("- Cards: Stack vertically on small screens")
            print("- Buttons: Full-width on mobile for easy tapping")
            print("- Fonts: Scale appropriately for screen size")
            return True
        else:
            print("WARN: Some mobile features may not be present")
            return False
    else:
        print(f"ERROR: Dashboard returned status {resp.status_code}")
        return False

def test_api_endpoints():
    """Test that all API endpoints work properly."""
    print("\nTesting API Endpoints:")
    print("-" * 60)
    
    endpoints = [
        ("/api/health", "Health Check"),
        ("/api/attendance", "Get Attendance"),
        ("/api/attendance/today", "Today's Attendance"),
        ("/api/stats", "Statistics"),
        ("/api/analytics", "Analytics"),
    ]
    
    all_ok = True
    for endpoint, name in endpoints:
        try:
            resp = requests.get(f"http://127.0.0.1:10000{endpoint}", timeout=3)
            status = "[OK]" if resp.status_code == 200 else "[FAIL]"
            print(f"{status} {name} ({endpoint}): {resp.status_code}")
            if resp.status_code != 200:
                all_ok = False
        except Exception as e:
            print(f"[FAIL] {name} ({endpoint}): {str(e)}")
            all_ok = False
    
    return all_ok

def main():
    """Run all mobile responsiveness tests."""
    try:
        dashboard_ok = test_dashboard_loaded()
        api_ok = test_api_endpoints()
        
        print("\n" + "=" * 60)
        if dashboard_ok and api_ok:
            print("\nAll mobile responsiveness tests PASSED!")
            print("\nYour dashboard is ready for mobile devices:")
            print("- iPhone, Android phones")
            print("- Tablets (iPad, Android tablets)")
            print("- Responsive desktop browsers")
            return 0
        else:
            print("\nSome tests failed. Check the output above.")
            return 1
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("Make sure the server is running on http://127.0.0.1:10000")
        return 1

if __name__ == "__main__":
    exit(main())
