#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Waiting for database..."
# Simple wait loop: try to run alembic current, retry on failure
until /app/.venv/bin/alembic current > /dev/null 2>&1; do
  echo "Database is unavailable or alembic check failed - sleeping"
  sleep 2
done

echo "Database is up - running migrations..."
/app/.venv/bin/alembic upgrade head

echo "Migrations applied successfully."

# Start uvicorn in background
echo "Starting uvicorn..."
/app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Wait for uvicorn to be ready (check port 8000)
echo "Waiting for uvicorn to be ready..."
until python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1', 8000))" 2>/dev/null; do
  echo "Uvicorn is not ready yet - sleeping"
  sleep 2
done

# Start celery worker with beat in background
echo "Starting celery..."
/app/.venv/bin/celery -A app.celery_app worker --loglevel=info -B &
CELERY_PID=$!

# Handle termination signals
trap "kill $UVICORN_PID $CELERY_PID; exit" SIGINT SIGTERM

# Wait for any process to exit
wait -n $UVICORN_PID $CELERY_PID

# If we get here, one of the processes exited, so kill the other
kill $UVICORN_PID $CELERY_PID 2>/dev/null