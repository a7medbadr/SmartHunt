"""add post_url to jobs

Revision ID: f4a1bc4f8e84
Revises: 3449cac338b9
Create Date: 2026-08-03 17:43:25.164670

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f4a1bc4f8e84"
down_revision: Union[str, Sequence[str], None] = "3449cac338b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("jobs", sa.Column("post_url", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("jobs", "post_url")
