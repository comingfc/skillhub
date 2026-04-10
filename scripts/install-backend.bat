@echo off
REM Install backend dependencies

cd /d %~dp0backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Backend dependencies installed successfully!
pause
