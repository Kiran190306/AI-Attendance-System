@echo off
echo ========================================
echo Starting AI Attendance System
echo ========================================

echo Checking virtual environment...
if not exist venv (
    echo ERROR: Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo.
echo Checking dataset folder...
if not exist dataset (
    echo ERROR: Dataset folder not found.
    echo Please run setup.bat to create required folders.
    pause
    exit /b 1
)

dir /b dataset >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Dataset folder is empty.
    echo Please run 'python capture_faces.py' to capture face data first.
    echo.
)

echo.
echo Checking camera availability...
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'No camera detected'); cap.release()"
if %errorlevel% neq 0 (
    echo WARNING: Camera check failed. Make sure a camera is connected.
)

echo.
echo Starting the system...
python run_system.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to start the system.
    pause
)

pause