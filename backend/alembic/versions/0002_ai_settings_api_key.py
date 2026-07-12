"""add openrouter_api_key to ai_settings (admin-settable from the UI)

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ai_settings",
        sa.Column("openrouter_api_key", sa.String(length=200), nullable=False,
                  server_default=""),
    )


def downgrade() -> None:
    op.drop_column("ai_settings", "openrouter_api_key")
