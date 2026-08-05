"""add posted_at to jobs

Revision ID: c5cf26a6abe7
Revises: caa0d837c7a0
Create Date: 2026-08-03 16:09:44.750000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c5cf26a6abe7"
down_revision: Union[str, Sequence[str], None] = "caa0d837c7a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("jobs", sa.Column("posted_at", sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("jobs", "posted_at")
