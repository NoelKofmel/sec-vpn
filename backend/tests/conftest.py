from collections.abc import AsyncGenerator

import pytest
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.database import Base, get_session
from app.core.redis import get_redis
from app.main import app


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    e = create_async_engine(settings.database_url)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield e
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await e.dispose()


@pytest.fixture(scope="session")
async def redis() -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[type-arg]
    # Use DB 1 to avoid polluting local dev Redis data
    url = settings.redis_url.rstrip("/")
    if not any(url.endswith(f"/{i}") for i in range(16)):
        url = f"{url}/1"
    client: aioredis.Redis = aioredis.from_url(url, decode_responses=True)  # type: ignore[type-arg]
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def client(
    db_session: AsyncSession,
    redis: aioredis.Redis,  # type: ignore[type-arg]
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_redis() -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[type-arg]
        yield redis

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = override_get_redis
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
