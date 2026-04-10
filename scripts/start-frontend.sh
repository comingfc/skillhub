#!/bin/bash
# Start frontend development server

cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "Dependencies not found. Running install-frontend.sh first..."
    bash "$(dirname "$0")/scripts/install-frontend.sh"
fi

echo "Starting frontend server on http://localhost:3000"
pnpm dev
