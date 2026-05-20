FROM python:3.13-slim

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

# Create /app directory and change ownership to appuser
RUN mkdir -p /app && chown appuser:appuser /app

WORKDIR /app

# Copy dependency files
COPY --chown=appuser:appuser requirements.txt ./

# Switch to appuser before installing dependencies
USER appuser

# Set HOME for appuser
ENV HOME=/app

# Install dependencies as appuser and create venv in /app/.venv
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Ensure the virtual environment is in the expected location
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code and start script
COPY --chown=appuser:appuser . .

# Make the start script executable
RUN chmod +x /app/start.sh

# Run the start script (waits for DB, runs migrations, then starts server)
CMD ["/app/start.sh"]
