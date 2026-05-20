#!/bin/sh
set -e

# Activate virtual environment created during build
. /app/.venv/bin/activate

echo "Running migrations..."
alembic upgrade head

echo "Starting uvicorn..."
uvicorn app.main:app --host 0.0.0.0 --port 8000

wait
