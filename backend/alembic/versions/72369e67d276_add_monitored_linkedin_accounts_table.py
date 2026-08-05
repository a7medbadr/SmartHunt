"""add monitored_linkedin_accounts table

Revision ID: 72369e67d276
Revises: f4a1bc4f8e84
Create Date: 2026-08-03 17:43:26.815612

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "72369e67d276"
down_revision: Union[str, Sequence[str], None] = "f4a1bc4f8e84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "monitored_linkedin_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_url", sa.String(length=500), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_url"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("monitored_linkedin_accounts")
