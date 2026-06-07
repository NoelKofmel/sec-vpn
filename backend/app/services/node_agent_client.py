import ssl
from pathlib import Path

import httpx
import structlog

from app.core.config import settings

log = structlog.get_logger(__name__)

_TIMEOUT = httpx.Timeout(10.0)


def _make_ssl_context() -> ssl.SSLContext | bool:
    ca = Path(settings.mtls_ca_cert)
    cert = Path(settings.mtls_client_cert)
    key = Path(settings.mtls_client_key)

    if not (ca.exists() and cert.exists() and key.exists()):
        log.warning(
            "node_agent.mtls_certs_missing",
            ca=str(ca),
            cert=str(cert),
            key=str(key),
        )
        return False  # skip TLS verification in dev when certs absent

    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(ca))
    ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
    return ctx


def _client(agent_url: str) -> httpx.AsyncClient:
    ssl_ctx = _make_ssl_context()
    return httpx.AsyncClient(
        base_url=agent_url,
        verify=ssl_ctx,
        timeout=_TIMEOUT,
    )


async def add_peer(
    agent_url: str,
    public_key: str,
    allowed_ips: str,
) -> None:
    async with _client(agent_url) as client:
        resp = await client.post(
            "/v1/peers",
            json={"public_key": public_key, "allowed_ips": allowed_ips},
        )
        resp.raise_for_status()
        log.info("node_agent.peer_added", agent=agent_url, pubkey=public_key[:12])


async def remove_peer(agent_url: str, public_key: str) -> None:
    async with _client(agent_url) as client:
        resp = await client.delete(f"/v1/peers/{public_key}")
        resp.raise_for_status()
        log.info("node_agent.peer_removed", agent=agent_url, pubkey=public_key[:12])


async def check_health(agent_url: str) -> bool:
    try:
        async with _client(agent_url) as client:
            resp = await client.get("/v1/health")
            return resp.status_code == 200
    except Exception as exc:
        log.warning("node_agent.health_check_failed", agent=agent_url, error=str(exc))
        return False
