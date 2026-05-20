import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def add_log_level(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Добавляет уровень логирования в event_dict."""
    if method_name == "warn":
        method_name = "warning"
    event_dict["level"] = method_name.upper()
    return event_dict


def human_readable_formatter(logger: Any, name: str, event_dict: dict) -> str:
    """
    Форматирует логи в удобочитаемый формат для человека.

    Пример вывода:
    [2026-05-20 14:30:45] INFO     | Сообщение события
        ├─ user_id: 12345
        ├─ action: create_ticket
        └─ duration: 0.123s
    """
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "INFO")
    event = event_dict.pop("event", "")

    # Основная строка лога
    log_parts = [f"[{timestamp}] {level:8} | {event}"]

    # Добавляем дополнительные поля, если они есть
    if event_dict:
        items = list(event_dict.items())
        for i, (key, value) in enumerate(items):
            # Используем разные символы для последнего элемента
            prefix = "    └─" if i == len(items) - 1 else "    ├─"

            # Форматируем значение
            if isinstance(value, (dict, list)):
                value_str = str(value)
            elif isinstance(value, float):
                # Для чисел с плавающей точкой ограничиваем количество знаков
                value_str = f"{value:.3f}"
            else:
                value_str = str(value)

            log_parts.append(f"{prefix} {key}: {value_str}")

    return "\n".join(log_parts)


def configure_logging(log_level: str = "INFO", log_file: str = "app.log") -> None:
    """Настраивает structlog для вывода логов в удобочитаемом формате."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Создаем file handler для записи в файл
    file_handler = logging.FileHandler(filename=log_path, encoding="utf-8")
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    # Создаем console handler с UTF-8 кодировкой
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # Принудительно устанавливаем UTF-8 для stdout (для Windows)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Настройка стандартного logging с выводом в файл и консоль
    logging.basicConfig(
        handlers=[file_handler, console_handler],
        level=logging.NOTSET,
        format="%(message)s",
    )

    # Настройка structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            add_log_level,
            human_readable_formatter,
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

        structlog.contextvars.bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)

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
