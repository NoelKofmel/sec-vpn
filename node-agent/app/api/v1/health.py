from fastapi import APIRouter

from app.core.config import settings
from app.schemas.peer import HealthResponse
from app.services import wireguard

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    up = await wireguard.interface_exists(settings.wg_interface)
    peer_count = await wireguard.get_peer_count(settings.wg_interface) if up else 0
    return HealthResponse(
        status="ok" if up else "degraded",
        wg_interface=settings.wg_interface,
        peer_count=peer_count,
    )
