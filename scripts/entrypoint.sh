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
    # RESTORING FULL APP: Single worker + standard asyncio loop for RAM stability
    # 512MB RAM is now dedicated to this single process
    exec uvicorn app.main:app --host "0.0.0.0" --port "$PORT" --log-level info --workers 1 --loop asyncio --timeout-keep-alive 75
fi
