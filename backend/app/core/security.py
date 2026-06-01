import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: int) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(user_id), "type": "refresh", "jti": jti, "exp": expire}
    token: str = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def decode_token(token: str) -> dict[str, object]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
