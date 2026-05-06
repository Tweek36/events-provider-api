#!/bin/sh
set -e

# Activate virtual environment
. /app/.venv/bin/activate

echo "Running migrations..."
alembic upgrade head

echo "Starting uvicorn and celery..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
celery -A app.celery_app worker --loglevel=info -B &

wait
