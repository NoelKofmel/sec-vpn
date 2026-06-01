from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends

from app.core.config import settings


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client: aioredis.Redis = aioredis.from_url(
        settings.redis_url, decode_responses=True
    )
    try:
        yield client
    finally:
        await client.aclose()


type RedisClient = Annotated[aioredis.Redis, Depends(get_redis)]
