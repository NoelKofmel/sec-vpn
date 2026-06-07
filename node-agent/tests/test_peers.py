from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

_PUBKEY = "wD7GQpCXZGjDy0TmXFM5+bH1cByj1KjpH9vBj2xSZAk="
_ALLOWED_IPS = "10.0.0.2/32"


@pytest.mark.asyncio
async def test_add_peer_success(client: AsyncClient) -> None:
    with patch(
        "app.api.v1.peers.wireguard.add_peer", new_callable=AsyncMock
    ) as mock_add:
        resp = await client.post(
            "/v1/peers",
            json={"public_key": _PUBKEY, "allowed_ips": _ALLOWED_IPS},
        )
    assert resp.status_code == 201
    assert resp.json()["public_key"] == _PUBKEY
    mock_add.assert_called_once()


@pytest.mark.asyncio
async def test_add_peer_wg_failure(client: AsyncClient) -> None:
    with patch(
        "app.api.v1.peers.wireguard.add_peer",
        new_callable=AsyncMock,
        side_effect=RuntimeError("wg not found"),
    ):
        resp = await client.post(
            "/v1/peers",
            json={"public_key": _PUBKEY, "allowed_ips": _ALLOWED_IPS},
        )
    assert resp.status_code == 503
    assert "WireGuard error" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_remove_peer_success(client: AsyncClient) -> None:
    with patch(
        "app.api.v1.peers.wireguard.remove_peer", new_callable=AsyncMock
    ) as mock_remove:
        resp = await client.delete(f"/v1/peers/{_PUBKEY}")
    assert resp.status_code == 204
    mock_remove.assert_called_once()


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    with (
        patch(
            "app.api.v1.health.wireguard.interface_exists",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.api.v1.health.wireguard.get_peer_count",
            new_callable=AsyncMock,
            return_value=3,
        ),
    ):
        resp = await client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["peer_count"] == 3


@pytest.mark.asyncio
async def test_health_degraded_when_wg_down(client: AsyncClient) -> None:
    with patch(
        "app.api.v1.health.wireguard.interface_exists",
        new_callable=AsyncMock,
        return_value=False,
    ):
        resp = await client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "degraded"
    assert resp.json()["peer_count"] == 0
