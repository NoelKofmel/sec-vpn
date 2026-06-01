import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import DBSession
from app.schemas.health import HealthResponse

log = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DBSession) -> HealthResponse:
    await db.execute(text("SELECT 1"))
    log.debug("health check passed")
    return HealthResponse(status="ok", database="connected")
