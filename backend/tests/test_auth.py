import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/register",
        json={"email": "test@example.com", "password": "securepassword"},
    )
    assert response.status_code == 201
    data = response.json()
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


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(
        "/v1/auth/register",
        json={"email": "login@example.com", "password": "securepassword"},
    )
    response = await client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "securepassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/v1/auth/register",
        json={"email": "wrongpw@example.com", "password": "securepassword"},
    )
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


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient) -> None:
    reg = await client.post(
        "/v1/auth/register",
        json={"email": "refresh@example.com", "password": "securepassword"},
    )
    refresh_token = reg.json()["refresh_token"]

    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] != refresh_token  # token was rotated


@pytest.mark.asyncio
async def test_refresh_token_reuse_rejected(client: AsyncClient) -> None:
    reg = await client.post(
        "/v1/auth/register",
        json={"email": "reuse@example.com", "password": "securepassword"},
    )
    refresh_token = reg.json()["refresh_token"]

    await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    # Second use of the same token must fail
    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    reg = await client.post(
        "/v1/auth/register",
        json={"email": "logout@example.com", "password": "securepassword"},
    )
    refresh_token = reg.json()["refresh_token"]

    logout = await client.post("/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 204

    # Token must be revoked
    response = await client.post(
        "/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401
