import structlog
from fastapi import APIRouter, HTTPException, status

from app.core.database import DBSession
from app.core.dependencies import AdminUser
from app.core.exceptions import ServerNotFoundError
from app.schemas.server import ServerCreate, ServerRead, ServerUpdate
from app.services.server_service import (
    create_server,
    delete_server,
    get_server,
    list_servers,
    update_server,
)

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/servers", tags=["servers"])


@router.get("", response_model=list[ServerRead])
async def get_servers(db: DBSession) -> list[ServerRead]:
    servers = await list_servers(db)
    return [ServerRead.model_validate(s) for s in servers]


@router.get("/{server_id}", response_model=ServerRead)
async def get_server_by_id(server_id: int, db: DBSession) -> ServerRead:
    try:
        server = await get_server(db, server_id)
    except ServerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        ) from exc
    return ServerRead.model_validate(server)


@router.post("", response_model=ServerRead, status_code=status.HTTP_201_CREATED)
async def create_server_endpoint(
    body: ServerCreate, db: DBSession, _admin: AdminUser
) -> ServerRead:
    server = await create_server(db, body)
    return ServerRead.model_validate(server)


@router.patch("/{server_id}", response_model=ServerRead)
async def update_server_endpoint(
    server_id: int, body: ServerUpdate, db: DBSession, _admin: AdminUser
) -> ServerRead:
    try:
        server = await update_server(db, server_id, body)
    except ServerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        ) from exc
    return ServerRead.model_validate(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server_endpoint(
    server_id: int, db: DBSession, _admin: AdminUser
) -> None:
    try:
        await delete_server(db, server_id)
    except ServerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Server not found"
        ) from exc
