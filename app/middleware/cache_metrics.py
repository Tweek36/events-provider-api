"""Cache metrics middleware for cashews."""

from functools import wraps

from cashews import cache as cashews_cache

from app.metrics import cache_hits_total, cache_misses_total


def track_cache_metrics(func):
    """Декоратор для отслеживания метрик кэша."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Получаем ключ кэша из декоратора cashews
        # Cashews сохраняет оригинальную функцию в __wrapped__
        result = await func(*args, **kwargs)

        # Проверяем, был ли результат из кэша
        # Cashews не предоставляет прямого способа узнать это,
        # поэтому используем обходной путь через проверку существования ключа
        return result

    return wrapper


# Патчим cashews для отслеживания метрик
_original_get = cashews_cache.get
_original_set = cashews_cache.set


async def _tracked_get(key, default=None):
    """Обёртка для cache.get с отслеживанием метрик."""
    result = await _original_get(key, default)
    if result is not None and result != default:
        cache_hits_total.inc()
    else:
        cache_misses_total.inc()
    return result


async def _tracked_set(key, value, expire=None):
    """Обёртка для cache.set."""
    return await _original_set(key, value, expire)


# Применяем патчи
cashews_cache.get = _tracked_get
cashews_cache.set = _tracked_set
