@echo off
REM Build script for Android APK (Windows)

echo ==========================================
echo AI Attendance System - Android Build
echo ==========================================
echo.

cd android_app

echo Cleaning previous builds...
call gradlew clean

echo Building debug APK...
call gradlew assembleDebug

echo Building release APK...
call gradlew assembleRelease

echo.
echo ==========================================
echo Build Complete!
echo ==========================================
echo.
echo Debug APK:   app\build\outputs\apk\debug\app-debug.apk
echo Release APK: app\build\outputs\apk\release\app-release.apk
echo.
echo To install debug APK:
echo   adb install app\build\outputs\apk\debug\app-debug.apk
echo.
pause
