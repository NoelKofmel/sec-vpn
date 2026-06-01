import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidCredentialsError, InvalidTokenError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.services.user_service import get_user_by_email, get_user_by_id

log = structlog.get_logger(__name__)

_PREFIX = "refresh:"


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    return user


async def issue_tokens(user_id: int, redis: Redis) -> tuple[str, str]:
    access_token = create_access_token(user_id)
    refresh_token, jti = create_refresh_token(user_id)
    ttl = settings.refresh_token_expire_days * 86400
    await redis.set(f"{_PREFIX}{jti}", str(user_id), ex=ttl)
    return access_token, refresh_token


async def rotate_refresh_token(
    refresh_token: str,
    db: AsyncSession,
    redis: Redis,
) -> tuple[str, str]:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise InvalidTokenError("Invalid refresh token") from exc

    if payload.get("type") != "refresh":
        raise InvalidTokenError("Not a refresh token")

    jti = str(payload.get("jti", ""))
    raw = await redis.getdel(f"{_PREFIX}{jti}")

    if not raw:
        raise InvalidTokenError("Refresh token revoked or expired")

    user = await get_user_by_id(db, int(str(raw)))
    if not user or not user.is_active:
        raise InvalidTokenError("User not found or inactive")

    log.info("auth.token_rotated", user_id=user.id)
    return await issue_tokens(user.id, redis)


async def revoke_refresh_token(refresh_token: str, redis: Redis) -> None:
    try:
        payload = decode_token(refresh_token)
        jti = str(payload.get("jti", ""))
        if jti:
            await redis.delete(f"{_PREFIX}{jti}")
    except Exception:
        pass  # best-effort; token may already be expired
