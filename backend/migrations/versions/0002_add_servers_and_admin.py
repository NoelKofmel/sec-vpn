"""add servers table and is_admin to users

Revision ID: a1b2c3d4e5f6
Revises: d4c3b2a1e5f6
Create Date: 2026-06-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "d4c3b2a1e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    op.create_table(
        "servers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("public_key", sa.String(length=64), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("agent_url", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", "maintenance", name="serverstatus"),
            nullable=False,
            server_default="inactive",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_key"),
    )
    op.create_index("ix_servers_country", "servers", ["country"])
    op.create_index("ix_servers_status", "servers", ["status"])


def downgrade() -> None:
    op.drop_index("ix_servers_status", table_name="servers")
    op.drop_index("ix_servers_country", table_name="servers")
    op.drop_table("servers")
    op.execute("DROP TYPE IF EXISTS serverstatus")
    op.drop_column("users", "is_admin")
