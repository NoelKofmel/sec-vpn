from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.models.server import ServerStatus


class ServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=2, max_length=2)
    city: str = Field(..., min_length=1, max_length=255)
    public_key: str = Field(..., min_length=44, max_length=64)
    endpoint: str = Field(..., min_length=1, max_length=255)
    agent_url: HttpUrl


class ServerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    country: str | None = Field(None, min_length=2, max_length=2)
    city: str | None = Field(None, min_length=1, max_length=255)
    public_key: str | None = Field(None, min_length=44, max_length=64)
    endpoint: str | None = Field(None, min_length=1, max_length=255)
    agent_url: HttpUrl | None = None
    status: ServerStatus | None = None


class ServerRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    country: str
    city: str
    public_key: str
    endpoint: str
    agent_url: str
    status: ServerStatus
    created_at: datetime
    updated_at: datetime
