#!/bin/bash
# Quick Start Script for Studio Génie Backend (Linux/Mac)

echo "========================================"
echo "Studio Génie Backend - Quick Start"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings."
    echo ""
    exit 1
fi

echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo "  1. Start Redis: redis-server"
echo "  2. Start API: uvicorn app.main:app --reload"
echo "  3. Start Worker: celery -A app.workers.celery_worker worker --loglevel=info"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
