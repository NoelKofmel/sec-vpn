import pytest
from httpx import AsyncClient

# ── helpers ──────────────────────────────────────────────────────────────────

async def register_user(client: AsyncClient, email: str) -> dict:
    resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "securepassword"},
    )
    assert resp.status_code == 201
    return resp.json()


# ── register ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    data = await register_user(client, "test@example.com")
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "dupe@example.com", "password": "securepassword"}
    await client.post("/v1/auth/register", json=payload)
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_password_too_short(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert response.status_code == 422


# ── login ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await register_user(client, "login@example.com")
    response = await client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "securepassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await register_user(client, "wrongpw@example.com")
    response = await client.post(
        "/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "securepassword"},
    )
    assert response.status_code == 401


# ── refresh ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient) -> None:
    data = await register_user(client, "refresh@example.com")
    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": data["refresh_token"]}
    )
    assert response.status_code == 200
    assert response.json()["refresh_token"] != data["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_reuse_rejected(client: AsyncClient) -> None:
    data = await register_user(client, "reuse@example.com")
    refresh_token = data["refresh_token"]
    await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": "not.a.valid.token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token_rejected(client: AsyncClient) -> None:
    data = await register_user(client, "wrongtype@example.com")
    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": data["access_token"]}
    )
    assert response.status_code == 401


# ── logout ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    data = await register_user(client, "logout@example.com")
    logout = await client.post(
        "/v1/auth/logout", json={"refresh_token": data["refresh_token"]}
    )
    assert logout.status_code == 204
    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": data["refresh_token"]}
    )
    assert response.status_code == 401


# ── me ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient) -> None:
    data = await register_user(client, "me@example.com")
    response = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me@example.com"
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient) -> None:
    response = await client.get("/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_refresh_token_rejected(client: AsyncClient) -> None:
    data = await register_user(client, "mewrong@example.com")
    response = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {data['refresh_token']}"},
    )
    assert response.status_code == 401
