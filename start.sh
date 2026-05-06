#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Waiting for database..."
# Simple wait loop: try to run alembic current, retry on failure
# This checks both connectivity and that alembic can connect.
until /app/.venv/bin/alembic current > /dev/null 2>&1; do
  echo "Database is unavailable or alembic check failed - sleeping"
  sleep 2
done

echo "Database is up - running migrations..."
/app/.venv/bin/alembic upgrade head

echo "Migrations applied successfully - starting server..."
exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000