FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

# Create /app directory and change ownership to appuser
RUN mkdir -p /app && chown appuser:appuser /app

WORKDIR /app

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Switch to appuser before installing dependencies
USER appuser

# Set HOME for appuser
ENV HOME=/app

# Install dependencies as appuser
RUN uv sync --frozen --no-dev

# Copy application code and start script
COPY --chown=appuser:appuser . .

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start script (waits for DB, runs migrations, then starts server)
CMD ["/app/start.sh"]
