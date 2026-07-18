"""add description and requirements columns to jobs

Revision ID: a1f9c3d7e2b4
Revises: 2c587f8db570
Create Date: 2026-07-26 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1f9c3d7e2b4"
down_revision: str | Sequence[str] | None = "2c587f8db570"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("requirements", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "requirements")
    op.drop_column("jobs", "description")
