@echo off
REM Start frontend development server

cd /d %~dp0frontend

if not exist "node_modules" (
    echo Dependencies not found. Running install-frontend.bat first...
    call "%~dp0install-frontend.bat"
)

echo Starting frontend server on http://localhost:3000
pnpm dev
