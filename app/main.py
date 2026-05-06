from fastapi import FastAPI
from app.api import sync, events, tickets
from cashews import cache
from app.config.logging import ProblematicRequestLoggingMiddleware, configure_logging
from app.settings import settings
from contextlib import asynccontextmanager

cache.setup(settings.REDIS_URL, prefix="my_app")
configure_logging(log_level="INFO", log_file="logs/app.log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.init()
    yield
    await cache.close()


app = FastAPI(title="Events Provider API", lifespan=lifespan)

app.add_middleware(ProblematicRequestLoggingMiddleware)

app.include_router(sync.router)
app.include_router(events.router)
app.include_router(tickets.router)

@app.get("/api/health")
def read_root():
    return {"status": "ok"}
