# ===================================================================
# AHP 2.0 — Unified Production Dockerfile
# Builds: Backend API + Doctor App + Patient App
# One container. One deployment. Everything works.
# ===================================================================

# --- STAGE 1: Build Doctor App (React/CRA) ---
FROM node:18-alpine AS doctor-build
WORKDIR /build

COPY doctor-app/package.json doctor-app/package-lock.json* ./
RUN npm install --legacy-peer-deps --ignore-scripts 2>/dev/null || npm install --legacy-peer-deps

COPY doctor-app/ .
# Empty string = relative URL (same domain as backend)
ENV REACT_APP_API_BASE_URL=""
ENV REACT_APP_WS_BASE_URL=""
RUN npm run build


# --- STAGE 2: Build Patient App (Expo Web) ---
FROM node:18-alpine AS patient-build
WORKDIR /build

COPY patient-app/package.json patient-app/package-lock.json* ./
RUN npm install 2>/dev/null || npm install --legacy-peer-deps

COPY patient-app/ .
# Empty string = relative URL (same domain as backend)
ENV EXPO_PUBLIC_API_BASE_URL=""
RUN npx expo export --platform web


# --- STAGE 3: Python Backend + Serve Everything ---
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.2 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
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
    poetry install --only main --no-interaction --no-ansi --no-root

# Copy backend source code
COPY app/ ./app/

# Copy built frontend apps from earlier stages
COPY --from=doctor-build /build/build /app/static/doctor
COPY --from=patient-build /build/dist /app/static/patient

# Create necessary directories
RUN mkdir -p /app/secure_uploads /app/uploads

# Expose port
EXPOSE 8080

# Start the unified server — Railway injects PORT as env var
CMD ["python", "-c", "import os; port = int(os.environ.get('PORT', 8080)); os.execvp('uvicorn', ['uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', str(port), '--log-level', 'info'])"]
