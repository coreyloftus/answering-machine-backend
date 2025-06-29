#!/bin/bash

# Startup script for the Answering Machine API

echo "Starting Answering Machine API..."

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
  echo "Error: src/main.py not found. Make sure you're in the correct directory."
  exit 1
fi

# Check if requirements are installed
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
  echo "Error: Required packages not installed. Run: pip install -r requirements.txt"
  exit 1
fi

# Set default port if not provided
export PORT=${PORT:-8080}

echo "Starting uvicorn server on port $PORT..."

# Start the application
exec uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 1
