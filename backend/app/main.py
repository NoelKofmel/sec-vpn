from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import health
from app.core.config import settings
from app.core.database import engine
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(settings.log_level)
    yield
    await engine.dispose()


app = FastAPI(
    title="SecVPN API",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/v1")
