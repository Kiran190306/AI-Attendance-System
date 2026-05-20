@echo off
echo ========================================
echo Starting AI Attendance System
echo ========================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/updating dependencies...
pip install -r requirements.txt

echo Initializing database...
python -c "from backend.database.db import init_db; init_db()"

echo Starting backend server...
start /B python run_production.py

echo Opening frontend in browser...
timeout /t 3 /nobreak > nul
python -c "import webbrowser; webbrowser.open('http://localhost:5000')"

echo System is running!
echo Press any key to stop...
pause > nul