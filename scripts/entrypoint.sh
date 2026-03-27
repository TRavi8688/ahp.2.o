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
    # NUCLEAR DEBUG: Running minimal app on IPv4/IPv6 dual stack
    exec uvicorn app.main_simple:app --host "::" --port "$PORT" --log-level debug --workers 1 --timeout-keep-alive 75
fi
