#!/bin/sh
set -e

echo "Activating virtual environment..."
. /app/.venv/bin/activate

echo "Running migrations..."
alembic upgrade head

echo "Starting uvicorn..."
# Celery worker и beat теперь запускаются внутри lifespan FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000
