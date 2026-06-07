import structlog
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.peer import PeerAdd, PeerResponse
from app.services import wireguard

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/peers", tags=["peers"])


@router.post("", response_model=PeerResponse, status_code=status.HTTP_201_CREATED)
async def add_peer(body: PeerAdd) -> PeerResponse:
    try:
        await wireguard.add_peer(
            settings.wg_interface, body.public_key, body.allowed_ips
        )
    except RuntimeError as exc:
        log.error("peers.add_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard error: {exc}",
        ) from exc
    return PeerResponse(public_key=body.public_key, allowed_ips=body.allowed_ips)


@router.delete("/{public_key}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_peer(public_key: str) -> None:
    try:
        await wireguard.remove_peer(settings.wg_interface, public_key)
    except RuntimeError as exc:
        log.error("peers.remove_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"WireGuard error: {exc}",
        ) from exc
