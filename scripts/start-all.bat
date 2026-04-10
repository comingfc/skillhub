@echo off
REM Install all dependencies and start both frontend and backend

echo ==========================================
echo SkillHub - Installing & Starting All Services
echo ==========================================

echo.
echo [1/2] Installing backend dependencies...
call "%~dp0install-backend.bat"

echo.
echo [2/2] Installing frontend dependencies...
call "%~dp0install-frontend.bat"

echo.
echo ==========================================
echo Starting services...
echo ==========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo ==========================================

cd /d %~dp0backend
call venv\Scripts\activate.bat
start "SkillHub Backend" uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

cd /d %~dp0frontend
start "SkillHub Frontend" pnpm dev
