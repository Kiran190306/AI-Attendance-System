#!/bin/bash

echo "========================================"
echo "AI Attendance System Setup"
echo "========================================"

echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.8+ (e.g., sudo apt install python3 python3-pip)"
    exit 1
fi

echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        exit 1
    fi
else
    echo "Virtual environment already exists."
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment."
    exit 1
fi

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    echo "Please check your internet connection and try again."
    exit 1
fi

echo ""
echo "Creating required folders..."
mkdir -p dataset
mkdir -p attendance
mkdir -p logs

echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "Run './run.sh' to start the system."
echo "========================================"