from pydantic import BaseModel, Field


class PeerAdd(BaseModel):
    public_key: str = Field(..., min_length=44, max_length=64)
    allowed_ips: str = Field(..., min_length=7)  # e.g. "10.0.0.2/32"


class PeerResponse(BaseModel):
    public_key: str
    allowed_ips: str


class HealthResponse(BaseModel):
    status: str
    wg_interface: str
    peer_count: int
