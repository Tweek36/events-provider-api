from contextlib import asynccontextmanager

from cashews import cache
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import events, sync, tickets
from app.config.logging import (ProblematicRequestLoggingMiddleware,
                                configure_logging)
from app.exceptions import EventsProviderError

configure_logging(log_level="INFO", log_file="logs/app.log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.setup("mem://")
    await cache.init()
    yield
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
