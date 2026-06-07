import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServerNotFoundError
from app.models.server import Server, ServerStatus
from app.schemas.server import ServerCreate, ServerUpdate

log = structlog.get_logger(__name__)


async def list_servers(db: AsyncSession) -> list[Server]:
    result = await db.execute(select(Server).order_by(Server.country, Server.name))
    return list(result.scalars().all())


async def get_server(db: AsyncSession, server_id: int) -> Server:
    server = await db.get(Server, server_id)
    if not server:
        raise ServerNotFoundError(server_id)
    return server


async def create_server(db: AsyncSession, body: ServerCreate) -> Server:
    server = Server(
        name=body.name,
        country=body.country.upper(),
        city=body.city,
        public_key=body.public_key,
        endpoint=body.endpoint,
        agent_url=str(body.agent_url),
        status=ServerStatus.inactive,
    )
    db.add(server)
    await db.commit()
    await db.refresh(server)
    log.info("server.created", server_id=server.id, name=server.name)
    return server


async def update_server(db: AsyncSession, server_id: int, body: ServerUpdate) -> Server:
    server = await get_server(db, server_id)
    updates = body.model_dump(exclude_none=True)
    if "agent_url" in updates:
        updates["agent_url"] = str(updates["agent_url"])
    for field, value in updates.items():
        setattr(server, field, value)
    await db.commit()
    await db.refresh(server)
    log.info("server.updated", server_id=server.id, fields=list(updates.keys()))
    return server


async def delete_server(db: AsyncSession, server_id: int) -> None:
    server = await get_server(db, server_id)
    await db.delete(server)
    await db.commit()
    log.info("server.deleted", server_id=server_id)


async def update_server_status(
    db: AsyncSession, server_id: int, status: ServerStatus
) -> None:
    server = await db.get(Server, server_id)
    if server and server.status != ServerStatus.maintenance:
        server.status = status
        await db.commit()
