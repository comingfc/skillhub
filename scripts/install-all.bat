@echo off
REM Install all dependencies (backend + frontend)

echo ==========================================
echo SkillHub - Installing Dependencies
echo ==========================================

echo.
echo [1/2] Backend dependencies...
call "%~dp0install-backend.bat"

echo.
echo [2/2] Frontend dependencies...
call "%~dp0install-frontend.bat"

echo.
echo ==========================================
echo All dependencies installed!
echo.
echo To start services:
echo   start-all.bat     - Start all
echo   start-backend.bat - Backend only
echo   start-frontend.bat - Frontend only
echo ==========================================
pause
