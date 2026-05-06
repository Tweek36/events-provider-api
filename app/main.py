from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api import sync, events, tickets
from cashews import cache
from app.config.logging import ProblematicRequestLoggingMiddleware, configure_logging
from contextlib import asynccontextmanager

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


@app.get("/api/health")
def health():
    return {"status": "ok"}
