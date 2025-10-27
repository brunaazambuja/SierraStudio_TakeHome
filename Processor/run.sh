#!/bin/bash

# Exit on error
set -e

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3.12 -m venv $VENV_DIR
fi

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

if [ -f "requirements.txt" ]; then
  echo "Installing dependencies..."
  pip install -r requirements.txt
fi

echo "Starting FastAPI app..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000