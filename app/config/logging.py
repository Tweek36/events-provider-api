import logging
import sys
from typing import Any

import structlog


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
    [2026-05-20 14:30:45] INFO | Сообщение события
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


def configure_logging(log_level: str = "INFO") -> None:
    """Настраивает structlog для вывода логов в удобочитаемом формате."""

    # Настройка стандартного logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
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
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
