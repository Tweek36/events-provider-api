#!/bin/sh
set -e

# Отключить кэш uv для избежания проблем с правами
export UV_NO_CACHE=1

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting uvicorn..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

wait
