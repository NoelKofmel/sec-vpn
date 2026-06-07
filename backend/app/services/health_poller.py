import asyncio

import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.server import Server, ServerStatus
from app.services import node_agent_client

log = structlog.get_logger(__name__)


async def _poll_once() -> None:
    async with async_session_factory() as db:
        result = await db.execute(
            select(Server).where(Server.status != ServerStatus.maintenance)
        )
        servers = list(result.scalars().all())

    for server in servers:
        reachable = await node_agent_client.check_health(server.agent_url)
        new_status = ServerStatus.active if reachable else ServerStatus.inactive
        if server.status != new_status:
            async with async_session_factory() as db:
                s = await db.get(Server, server.id)
                if s and s.status != ServerStatus.maintenance:
                    s.status = new_status
                    await db.commit()
            log.info(
                "health_poller.status_changed",
                server_id=server.id,
                name=server.name,
                status=new_status,
            )


async def run_health_poller() -> None:
    log.info("health_poller.started", interval=settings.health_check_interval)
    while True:
        try:
            await _poll_once()
        except Exception as exc:
            log.error("health_poller.error", error=str(exc))
        await asyncio.sleep(settings.health_check_interval)
