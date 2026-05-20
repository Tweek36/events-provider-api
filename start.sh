#!/bin/sh
set -e

echo "Activating virtual environment..."
. /app/.venv/bin/activate

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting uvicorn and celery..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
uv run celery -A app.celery_app worker --loglevel=info -B &
0
