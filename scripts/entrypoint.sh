#!/bin/bash
set -e

# Default to API if not specified
SERVICE_TYPE=${SERVICE_TYPE:-api}
PORT=${PORT:-8080}

if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "🚀 Starting Mulajna Arq Worker..."
    exec python start_worker.py
else
    echo "🌐 Starting Mulajna API on port $PORT..."
    # Reducing workers to 2 and forcing asyncio loop for stability
    # Increased keep-alive to 75s to prevent Railway proxy timeouts
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info --workers 2 --loop asyncio --timeout-keep-alive 75
fi
