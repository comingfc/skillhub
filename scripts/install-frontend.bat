@echo off
REM Install frontend dependencies using pnpm

cd /d %~dp0frontend

echo Checking pnpm...
where pnpm >nul 2>nul
if errorlevel 1 (
    echo pnpm not found, installing...
    npm install -g pnpm
)

echo Installing frontend dependencies...
pnpm install

echo Frontend dependencies installed successfully!
pause
