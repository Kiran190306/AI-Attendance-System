#!/usr/bin/env python3
"""
Test Login System - Verify authentication works

This script tests the new login system functionality.
"""

import requests
import json

def test_redirect_to_login():
    """Test that dashboard redirects to login when not authenticated."""
    print("🔍 Testing Dashboard Redirect...")

    try:
        response = requests.get("http://localhost:10000/dashboard", allow_redirects=False, timeout=5)
        if response.status_code == 302:  # Redirect
            location = response.headers.get('Location', '')
            if 'login' in location:
                print("✅ Dashboard correctly redirects to login")
                return True
            else:
                print(f"❌ Unexpected redirect to: {location}")
                return False
        else:
            print(f"❌ Expected redirect, got status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Redirect test error: {str(e)}")
        return False

def test_login_page_access():
    """Test that login page is accessible."""
    print("\n🔍 Testing Login Page Access...")

    try:
        response = requests.get("http://localhost:10000/login", timeout=5)
        if response.status_code == 200:
            if "AI Attendance System" in response.text and "login-form" in response.text:
                print("✅ Login page accessible and contains form")
                return True
            else:
                print("❌ Login page missing expected content")
                return False
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login page error: {str(e)}")
        return False

def test_successful_login():
    """Test successful login with correct credentials."""
    print("\n🔍 Testing Successful Login...")

    try:
        # Create a session to maintain cookies
        session = requests.Session()

        # First get the login page to establish session
        session.get("http://localhost:10000/login", timeout=5)

        # Now login with correct credentials
        login_data = {
            "username": "admin",
            "password": "1234"
        }
        response = session.post("http://localhost:10000/login", data=login_data, allow_redirects=False, timeout=5)

        if response.status_code == 302:  # Redirect after successful login
            location = response.headers.get('Location', '')
            if 'dashboard' in location:
                print("✅ Login successful, redirected to dashboard")
                return True, session
            else:
                print(f"❌ Unexpected redirect after login: {location}")
                return False, None
        else:
            print(f"❌ Login failed with status: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Login test error: {str(e)}")
        return False, None

def test_dashboard_access_after_login(session):
    """Test dashboard access after successful login."""
    print("\n🔍 Testing Dashboard Access After Login...")

    try:
        response = session.get("http://localhost:10000/dashboard", timeout=5)
        if response.status_code == 200:
            if "AI Attendance System" in response.text and "Logout" in response.text:
                print("✅ Dashboard accessible after login with logout button")
                return True
            else:
                print("❌ Dashboard missing expected content")
                return False
        else:
            print(f"❌ Dashboard access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard access error: {str(e)}")
        return False

def test_failed_login():
    """Test login with wrong credentials."""
    print("\n🔍 Testing Failed Login...")

    try:
        session = requests.Session()
        session.get("http://localhost:10000/login", timeout=5)

        login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        response = session.post("http://localhost:10000/login", data=login_data, timeout=5)

        if response.status_code == 200 and "Invalid username or password" in response.text:
            print("✅ Failed login correctly shows error message")
            return True
        else:
            print(f"❌ Failed login test failed: status={response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed login test error: {str(e)}")
        return False

def test_logout():
    """Test logout functionality."""
    print("\n🔍 Testing Logout...")

    try:
        # Login first
        session = requests.Session()
        session.get("http://localhost:10000/login", timeout=5)

        login_data = {"username": "admin", "password": "1234"}
        session.post("http://localhost:10000/login", data=login_data, timeout=5)

        # Now logout
        response = session.get("http://localhost:10000/logout", allow_redirects=False, timeout=5)

        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'login' in location:
                print("✅ Logout successful, redirected to login")
                return True
            else:
                print(f"❌ Unexpected redirect after logout: {location}")
                return False
        else:
            print(f"❌ Logout failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Logout test error: {str(e)}")
        return False

def main():
    """Run all login system tests."""
    print("=" * 60)
    print("🔐 Login System - Test Suite")
    print("=" * 60)

    # Test 1: Redirect to login
    redirect_ok = test_redirect_to_login()

    # Test 2: Login page access
    login_page_ok = test_login_page_access()

    # Test 3: Successful login
    login_ok, session = test_successful_login()

    # Test 4: Dashboard access after login
    dashboard_ok = False
    if login_ok and session:
        dashboard_ok = test_dashboard_access_after_login(session)

    # Test 5: Failed login
    failed_login_ok = test_failed_login()

    # Test 6: Logout
    logout_ok = test_logout()

    print("\n" + "=" * 60)
    print("📋 Test Results:")
    print(f"   Dashboard Redirect: {'✅ PASS' if redirect_ok else '❌ FAIL'}")
    print(f"   Login Page Access: {'✅ PASS' if login_page_ok else '❌ FAIL'}")
    print(f"   Successful Login: {'✅ PASS' if login_ok else '❌ FAIL'}")
    print(f"   Dashboard Access: {'✅ PASS' if dashboard_ok else '❌ FAIL'}")
    print(f"   Failed Login: {'✅ PASS' if failed_login_ok else '❌ FAIL'}")
    print(f"   Logout: {'✅ PASS' if logout_ok else '❌ FAIL'}")

    if all([redirect_ok, login_page_ok, login_ok, dashboard_ok, failed_login_ok, logout_ok]):
        print("\n🎉 All login system tests passed!")
        print("\n📱 Access the system:")
        print("   Login Page: http://localhost:10000/login")
        print("   Demo Credentials: admin / 1234")
    else:
        print("\n⚠️  Some tests failed. Check server logs.")

    print("=" * 60)

if __name__ == "__main__":
    main()
