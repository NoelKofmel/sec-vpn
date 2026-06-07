import asyncio
import shutil

import structlog

log = structlog.get_logger(__name__)

_WG = shutil.which("wg")


def _wg_available() -> bool:
    return _WG is not None


async def _run(args: list[str]) -> str:
    if not _wg_available():
        raise RuntimeError("wg binary not found; wireguard-tools not installed")
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode().strip())
    return stdout.decode().strip()


async def add_peer(interface: str, public_key: str, allowed_ips: str) -> None:
    await _run(
        [
            "wg",
            "set",
            interface,
            "peer",
            public_key,
            "allowed-ips",
            allowed_ips,
        ]
    )
    log.info("wg.peer_added", interface=interface, pubkey=public_key[:12])


async def remove_peer(interface: str, public_key: str) -> None:
    await _run(["wg", "set", interface, "peer", public_key, "remove"])
    log.info("wg.peer_removed", interface=interface, pubkey=public_key[:12])


async def get_peer_count(interface: str) -> int:
    try:
        output = await _run(["wg", "show", interface, "peers"])
        if not output:
            return 0
        return len(output.splitlines())
    except Exception:
        return 0


async def interface_exists(interface: str) -> bool:
    try:
        await _run(["wg", "show", interface])
        return True
    except Exception:
        return False
