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
    # Reducing workers to 2 to stay within Railway's 512MB RAM limit
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info --workers 2
fi
