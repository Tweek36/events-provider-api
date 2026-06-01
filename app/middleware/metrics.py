"""Metrics collection middleware."""

import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.metrics import http_request_duration_seconds, http_requests_total


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware для автоматического сбора HTTP метрик."""

    async def dispatch(self, request, call_next):
        # Пропускаем сам эндпоинт /metrics, чтобы не создавать рекурсию
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start_time

        # Собираем метрики
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response
