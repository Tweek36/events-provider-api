import asyncio
from contextlib import asynccontextmanager

import sentry_sdk
from cashews import cache
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import REGISTRY, generate_latest
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import events, sync, tickets
from app.config.logging import ProblematicRequestLoggingMiddleware, configure_logging
from app.database import get_session
from app.exceptions import EventsProviderError
from app.metrics import events_total, tickets_cancelled_total, tickets_created_total
from app.middleware import cache_metrics  # noqa: F401 - импорт для применения патчей
from app.middleware.metrics import MetricsMiddleware
from app.repositories.event import EventRepository
from app.repositories.ticket import TicketRepository
from app.settings import settings
from app.workers.celery_worker import celery_worker
from app.workers.outbox_worker import outbox_worker

configure_logging(log_level="INFO", log_file="logs/app.log")

# Инициализация Sentry/GlitchTip
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[FastApiIntegration()],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.setup("mem://")
    await cache.init()

    # Запустить Celery worker и beat
    await celery_worker.start()

    # Запустить outbox worker
    await outbox_worker.start()

    yield

    # Остановить workers
    await outbox_worker.stop()
    await celery_worker.stop()
    await cache.close()


app = FastAPI(title="Events Provider API", lifespan=lifespan)

# Регистрируем middleware (порядок важен - MetricsMiddleware должен быть первым)
app.add_middleware(MetricsMiddleware)
app.add_middleware(ProblematicRequestLoggingMiddleware)

app.include_router(sync.router)
app.include_router(events.router)
app.include_router(tickets.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


@app.exception_handler(EventsProviderError)
async def events_provider_exception_handler(request, exc: EventsProviderError):
    return JSONResponse(
        status_code=502,
        content={"detail": f"Events provider error: {exc.detail}"},
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics(session: AsyncSession = Depends(get_session)):
    """Эндпоинт для Prometheus метрик."""
    # Обновляем бизнес-метрики из БД
    event_repo = EventRepository(session)
    ticket_repo = TicketRepository(session)

    # Выполняем запросы параллельно
    counts = await asyncio.gather(
        event_repo.count_all(),
        ticket_repo.count_all(),
        ticket_repo.count_cancelled(),
    )

    events_total.set(counts[0])
    tickets_created_total.set(counts[1])
    tickets_cancelled_total.set(counts[2])

    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain",
    )
