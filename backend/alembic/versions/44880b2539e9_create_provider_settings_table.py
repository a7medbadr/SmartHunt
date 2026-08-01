"""create provider_settings table

Revision ID: 44880b2539e9
Revises: e90b9681afe8
Create Date: 2026-08-01 13:07:42.604170

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "44880b2539e9"
down_revision: Union[str, Sequence[str], None] = "e90b9681afe8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Scoped to just provider_settings — autogenerate also picked up
    # pre-existing unrelated schema drift (search_history, jobs column
    # types, misc indexes) that isn't part of this change; left alone.
    op.create_table(
        "provider_settings",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("provider_settings")
