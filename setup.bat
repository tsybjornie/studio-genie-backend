@echo off
REM Quick Start Script for Studio Génie Backend (Windows)

echo ========================================
echo Studio Génie Backend - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and configure your settings.
    echo.
    pause
    exit /b 1
)

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To start the application:
echo   1. Start Redis: docker run -d -p 6379:6379 redis
echo   2. Start API: uvicorn app.main:app --reload
echo   3. Start Worker: celery -A app.workers.celery_worker worker --loglevel=info
echo.
echo API will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
pause
