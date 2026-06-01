import structlog
from fastapi import APIRouter, HTTPException, Request, status

from app.core.database import DBSession
from app.core.dependencies import CurrentUser
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.limiter import limiter
from app.core.redis import RedisClient
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import (
    authenticate_user,
    issue_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.services.user_service import create_user

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def register(
    request: Request, body: RegisterRequest, db: DBSession, redis: RedisClient
) -> TokenResponse:
    try:
        user = await create_user(db, body.email, body.password)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc
    access_token, refresh_token = await issue_tokens(user.id, redis)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request, body: LoginRequest, db: DBSession, redis: RedisClient
) -> TokenResponse:
    try:
        user = await authenticate_user(db, body.email, body.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc
    access_token, refresh_token = await issue_tokens(user.id, redis)
    log.info("auth.login", user_id=user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest, db: DBSession, redis: RedisClient
) -> TokenResponse:
    try:
        access_token, refresh_token = await rotate_refresh_token(
            body.refresh_token, db, redis
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, redis: RedisClient) -> None:
    await revoke_refresh_token(body.refresh_token, redis)


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
