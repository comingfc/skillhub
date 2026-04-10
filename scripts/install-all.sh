#!/bin/bash
# Install all dependencies (backend + frontend)

echo "=========================================="
echo "SkillHub - Installing Dependencies"
echo "=========================================="

echo ""
echo "[1/2] Backend dependencies..."
bash "$(dirname "$0")/scripts/install-backend.sh"

echo ""
echo "[2/2] Frontend dependencies..."
bash "$(dirname "$0")/scripts/install-frontend.sh"

echo ""
echo "=========================================="
echo "All dependencies installed!"
echo ""
echo "To start services:"
echo "  ./scripts/start-all.sh    # Start all"
echo "  ./scripts/start-backend.sh # Backend only"
echo "  ./scripts/start-frontend.sh # Frontend only"
echo "=========================================="
