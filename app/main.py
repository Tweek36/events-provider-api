from contextlib import asynccontextmanager

import sentry_sdk
from cashews import cache
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.api import events, sync, tickets
from app.config.logging import ProblematicRequestLoggingMiddleware, configure_logging
from app.exceptions import EventsProviderError
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
