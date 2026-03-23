@echo off
REM ═════════════════════════════════════════════════════════════════════════════
REM BUGVORTEX AI - QUICK START SCRIPT (Windows)
REM This script automates the setup and running of the project
REM ═════════════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo ╔═════════════════════════════════════════════════════════════════════════╗
echo ║                    BUGVORTEX AI - QUICK START                           ║
echo ║              Semantic Bug & Exception Predictor v1.0                    ║
echo ╚═════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Check if virtual environment exists
if not exist "venv" (
    echo.
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
)

REM Activate virtual environment
echo.
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated

REM Install dependencies
echo.
echo [INFO] Installing dependencies (this may take 5-10 minutes first time)...
pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

REM Check if model exists
if not exist "saved_bug_predictor_model" (
    echo.
    echo [INFO] Model not found. Training model...
    echo This may take 5-15 minutes depending on your CPU/GPU
    echo.
    python model_trainer.py
    if errorlevel 1 (
        echo [ERROR] Model training failed
        pause
        exit /b 1
    )
    echo ✓ Model trained and saved
)

REM Start the API server
echo.
echo ╔═════════════════════════════════════════════════════════════════════════╗
echo ║              STARTING BUGVORTEX AI API SERVER                           ║
echo ╠═════════════════════════════════════════════════════════════════════════╣
echo ║                                                                         ║
echo ║  Dashboard:  http://localhost:8000                                      ║
echo ║  API Docs:   http://localhost:8000/docs                                 ║
echo ║  Status:     http://localhost:8000/status                               ║
echo ║                                                                         ║
echo ║  The server will start momentarily. Press Ctrl+C to stop.               ║
echo ║                                                                         ║
echo ╚═════════════════════════════════════════════════════════════════════════╝
echo.

python api_server.py

pause
