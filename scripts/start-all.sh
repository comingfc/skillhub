#!/bin/bash
# Install all dependencies and start both frontend and backend

echo "=========================================="
echo "SkillHub - Installing & Starting All Services"
echo "=========================================="

# Install backend
echo ""
echo "[1/2] Installing backend dependencies..."
bash "$(dirname "$0")/scripts/install-backend.sh"

# Install frontend
echo ""
echo "[2/2] Installing frontend dependencies..."
bash "$(dirname "$0")/scripts/install-frontend.sh"

echo ""
echo "=========================================="
echo "Starting services..."
echo "=========================================="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

# Start backend in background
cd "$(dirname "$0")/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd "$(dirname "$0")/frontend"
pnpm dev &
FRONTEND_PID=$!

# Wait for either process
wait
