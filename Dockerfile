FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set uv cache directory
ENV UV_CACHE_DIR=/tmp/uv-cache

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

# Create /app directory and change ownership to appuser
RUN mkdir -p /app && chown appuser:appuser /app

WORKDIR /app

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Install dependencies using uv as root (to avoid permission issues)
RUN uv sync --frozen --no-dev

# Switch to appuser for all subsequent operations
USER appuser

# Copy application code and start script
COPY --chown=appuser:appuser . .

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start script (waits for DB, runs migrations, then starts server)
CMD ["/app/start.sh"]
