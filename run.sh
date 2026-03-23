#!/bin/bash

# ═════════════════════════════════════════════════════════════════════════════
# BUGVORTEX AI - QUICK START SCRIPT (Linux/Mac)
# This script automates the setup and running of the project
# ═════════════════════════════════════════════════════════════════════════════

echo ""
echo "╔═════════════════════════════════════════════════════════════════════════╗"
echo "║                    BUGVORTEX AI - QUICK START                           ║"
echo "║              Semantic Bug & Exception Predictor v1.0                    ║"
echo "╚═════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python from https://www.python.org"
    exit 1
fi

echo "✓ Python found"
python3 --version

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo ""
echo "[INFO] Installing dependencies (this may take 5-10 minutes first time)..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"

# Check if model exists
if [ ! -d "saved_bug_predictor_model" ]; then
    echo ""
    echo "[INFO] Model not found. Training model..."
    echo "This may take 5-15 minutes depending on your CPU/GPU"
    echo ""
    python3 model_trainer.py
    if [ $? -ne 0 ]; then
        echo "[ERROR] Model training failed"
        exit 1
    fi
    echo "✓ Model trained and saved"
fi

# Start the API server
echo ""
echo "╔═════════════════════════════════════════════════════════════════════════╗"
echo "║              STARTING BUGVORTEX AI API SERVER                           ║"
echo "╠═════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                         ║"
echo "║  Dashboard:  http://localhost:8000                                      ║"
echo "║  API Docs:   http://localhost:8000/docs                                 ║"
echo "║  Status:     http://localhost:8000/status                               ║"
echo "║                                                                         ║"
echo "║  The server will start momentarily. Press Ctrl+C to stop.               ║"
echo "║                                                                         ║"
echo "╚═════════════════════════════════════════════════════════════════════════╝"
echo ""

python3 main.py
