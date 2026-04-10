@echo off
REM Start backend server

cd /d %~dp0backend

if not exist "venv" (
    echo Virtual environment not found. Running install-backend.bat first...
    call "%~dp0install-backend.bat"
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting backend server on http://0.0.0.0:8000
echo API docs: http://localhost:8000/docs
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
