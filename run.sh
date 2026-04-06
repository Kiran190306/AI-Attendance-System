#!/bin/bash

echo "========================================"
echo "Starting AI Attendance System"
echo "========================================"

echo "Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment."
    exit 1
fi

echo ""
echo "Checking dataset folder..."
if [ ! -d "dataset" ]; then
    echo "ERROR: Dataset folder not found."
    echo "Please run ./setup.sh to create required folders."
    exit 1
fi

if [ -z "$(ls -A dataset)" ]; then
    echo "WARNING: Dataset folder is empty."
    echo "Please run 'python capture_faces.py' to capture face data first."
    echo ""
fi

echo ""
echo "Checking camera availability..."
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'No camera detected'); cap.release()"

echo ""
echo "Starting the system..."
python3 run_system.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start the system."
fi