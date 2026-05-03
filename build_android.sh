#!/usr/bin/env bash
# Build script for Android APK

set -e

echo "=========================================="
echo "AI Attendance System - Android Build"
echo "=========================================="

# Navigate to android_app
cd android_app

echo "Cleaning previous builds..."
./gradlew clean

echo "Building debug APK..."
./gradlew assembleDebug

echo "Building release APK..."
./gradlew assembleRelease

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""
echo "Debug APK:   app/build/outputs/apk/debug/app-debug.apk"
echo "Release APK: app/build/outputs/apk/release/app-release.apk"
echo ""
echo "To install debug APK:"
echo "  adb install app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "To create signed release APK:"
echo "  1. Build → Generate Signed Bundle/APK in Android Studio"
echo "  2. Follow the wizard and select 'release' build type"
echo ""
