import logging
import uuid
from pathlib import Path
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import time
from starlette.responses import Response

def configure_logging(log_level: str = "INFO", log_file: str = "app.log") -> None:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(filename=log_path, encoding="utf-8")
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    file_handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(
        handlers=[file_handler],
        level=logging.NOTSET,
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class ProblematicRequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        request_id = str(uuid.uuid4())

        structlog.contextvars.bind_contextvars(
            request_id=request_id, method=request.method, path=request.url.path
        )

        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            logger = structlog.get_logger()
            logger.error(
                "unhandled_exception",
                error_type=type(e).__name__,
                error_msg=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            raise e

        duration = time.time() - start_time

        if response.status_code >= 400:
            logger = structlog.get_logger()

            logger.warning(
                "problematic_request_metadata",
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                user_agent=request.headers.get("user-agent", "unknown"),
                query_params=dict(request.query_params),
            )

        return response
