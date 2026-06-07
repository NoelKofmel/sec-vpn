import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user_service import create_user


async def _make_admin(db: AsyncSession, email: str, password: str) -> User:
    user = await create_user(db, email, password)
    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    return user


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        "/v1/auth/login", json={"email": email, "password": password}
    )
    return str(resp.json()["access_token"])


_SERVER_PAYLOAD = {
    "name": "Frankfurt 01",
    "country": "DE",
    "city": "Frankfurt",
    "public_key": "wD7GQpCXZGjDy0TmXFM5+bH1cByj1KjpH9vBj2xSZAk=",
    "endpoint": "1.2.3.4:51820",
    "agent_url": "http://1.2.3.4:8001",
}


@pytest.mark.asyncio
async def test_list_servers_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/v1/servers")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_server_requires_admin(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_user(db_session, "user_nonadmin@example.com", "password123")
    token = await _login(client, "user_nonadmin@example.com", "password123")
    resp = await client.post(
        "/v1/servers",
        json=_SERVER_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_server_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/v1/servers", json=_SERVER_PAYLOAD)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_and_get_server(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_admin(db_session, "admin@example.com", "adminpass123")
    token = await _login(client, "admin@example.com", "adminpass123")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/v1/servers", json=_SERVER_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Frankfurt 01"
    assert data["country"] == "DE"
    assert data["status"] == "inactive"
    server_id = data["id"]

    resp = await client.get(f"/v1/servers/{server_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == server_id


@pytest.mark.asyncio
async def test_update_server(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_admin(db_session, "admin2@example.com", "adminpass123")
    token = await _login(client, "admin2@example.com", "adminpass123")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {**_SERVER_PAYLOAD, "public_key": "xE8HRqDYHJkEz1UnGGN6+cI2dCzk2LkqI0wCk3yTahs="}
    create_resp = await client.post("/v1/servers", json=payload, headers=headers)
    server_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/v1/servers/{server_id}",
        json={"status": "maintenance", "name": "Frankfurt 01 (updated)"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "maintenance"
    assert resp.json()["name"] == "Frankfurt 01 (updated)"


@pytest.mark.asyncio
async def test_delete_server(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_admin(db_session, "admin3@example.com", "adminpass123")
    token = await _login(client, "admin3@example.com", "adminpass123")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {**_SERVER_PAYLOAD, "public_key": "yF9ISrEZIKlFa2VoHHO7+dJ3eDal3MlrJ1xDl4zUbit="}
    create_resp = await client.post("/v1/servers", json=payload, headers=headers)
    server_id = create_resp.json()["id"]

    resp = await client.delete(f"/v1/servers/{server_id}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get(f"/v1/servers/{server_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_server(client: AsyncClient) -> None:
    resp = await client.get("/v1/servers/99999")
    assert resp.status_code == 404
