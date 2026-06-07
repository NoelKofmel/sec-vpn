from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ServerStatus(StrEnum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_url: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ServerStatus] = mapped_column(
        Enum(ServerStatus), nullable=False, default=ServerStatus.inactive
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
