#!/bin/bash
# Install backend dependencies

cd "$(dirname "$0")/backend"

echo "Creating virtual environment..."
python -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Backend dependencies installed successfully!"
echo "To activate: source venv/bin/activate"
