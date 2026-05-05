FROM python:3.11-slim

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

# Create /app directory and change ownership to appuser
RUN mkdir -p /app && chown appuser:appuser /app

# Switch to appuser for all subsequent operations
USER appuser

WORKDIR /app

# Copy requirements file
COPY --chown=appuser:appuser requirements.txt ./

# Create virtual environment and install dependencies using pip
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application code and start script
COPY --chown=appuser:appuser . .

# Run the application directly with uvicorn
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
