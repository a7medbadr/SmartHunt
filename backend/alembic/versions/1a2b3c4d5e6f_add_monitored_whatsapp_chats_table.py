"""add monitored_whatsapp_chats table

Revision ID: 1a2b3c4d5e6f
Revises: e25fa514e5a8
Create Date: 2026-08-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, Sequence[str], None] = "e25fa514e5a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "monitored_whatsapp_chats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_url", sa.String(length=500), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("chat_type", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_url"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("monitored_whatsapp_chats")
