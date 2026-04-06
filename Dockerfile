# ===================================================================
# AHP 2.0 — Pure API & AI Worker (Unified Engine)
# Optimized for Three-Lane Highway Architecture
# ===================================================================

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.2 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (Heavy dependencies for AI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Copy backend dependencies
COPY pyproject.toml poetry.lock* README.md* ./
RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main --no-interaction --no-ansi --no-root

# Copy backend source code
COPY app/ ./app/

# Create necessary directories for health-checks and secure processing
RUN mkdir -p /app/secure_uploads /app/uploads

# Expose the default port (overridden by Railway $PORT)
EXPOSE 8080

# Command is provided by railway.toml (api vs worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
