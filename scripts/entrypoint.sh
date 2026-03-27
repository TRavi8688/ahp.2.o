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
    echo "🔍 DEBUG: Environment PORT is: $PORT"
    # Reverting to IPv4 only for maximum proxy compatibility
    # Explicitly using a hardcoded default if PORT is missing
    TARGET_PORT=${PORT:-8080}
    echo "📻 Binding to 0.0.0.0:$TARGET_PORT"
    exec uvicorn app.main_simple:app --host "0.0.0.0" --port "$TARGET_PORT" --log-level debug --workers 1 --timeout-keep-alive 75
fi
