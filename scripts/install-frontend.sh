#!/bin/bash
# Install frontend dependencies using pnpm

cd "$(dirname "$0")/frontend"

echo "Checking pnpm..."
if ! command -v pnpm &> /dev/null; then
    echo "pnpm not found, installing..."
    npm install -g pnpm
fi

echo "Installing frontend dependencies..."
pnpm install

echo "Frontend dependencies installed successfully!"
