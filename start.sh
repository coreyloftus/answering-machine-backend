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

# Check for required environment variables and set defaults if missing
echo "Checking environment variables..."

# Set default values for required env vars to prevent crashes
export GEMINI_API_KEY=${GEMINI_API_KEY:-""}
export SERVICE_ACCOUNT_KEY_JSON=${SERVICE_ACCOUNT_KEY_JSON:-""}
export GCS_STORAGE_BUCKET=${GCS_STORAGE_BUCKET:-""}
export TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID:-""}
export TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN:-""}
export TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER:-""}

echo "Starting uvicorn server on port $PORT..."

# Start the application with better error handling
exec uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info
