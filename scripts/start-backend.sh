#!/bin/bash
# Start backend server

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running install-backend.sh first..."
    bash "$(dirname "$0")/scripts/install-backend.sh"
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting backend server on http://0.0.0.0:8000"
echo "API docs: http://localhost:8000/docs"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
