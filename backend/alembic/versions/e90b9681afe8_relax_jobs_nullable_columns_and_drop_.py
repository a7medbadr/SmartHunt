"""relax jobs nullable columns and drop stale url unique constraint

The Job model has declared location/source/url as nullable=True (and
has no unique constraint on url) for a while, but the original
migration that created the jobs table never caught up — url in
particular being NOT NULL + UNIQUE broke job discovery outright, since
several provider stubs return jobs with no url at all, and forcing a
placeholder empty string collided against the unique constraint.

Revision ID: e90b9681afe8
Revises: d8e3a1bd9195
Create Date: 2026-08-01 01:06:23.803092

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e90b9681afe8"
down_revision: Union[str, Sequence[str], None] = "d8e3a1bd9195"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("jobs", "location", existing_type=sa.String(), nullable=True)
    op.alter_column("jobs", "source", existing_type=sa.String(), nullable=True)
    op.alter_column("jobs", "url", existing_type=sa.String(), nullable=True)
    # Some environments already had this constraint dropped out-of-band
    # (pre-existing drift) — IF EXISTS makes this safe either way.
    op.execute("ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_url_key")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint("jobs_url_key", "jobs", ["url"])
    op.alter_column("jobs", "url", existing_type=sa.String(), nullable=False)
    op.alter_column("jobs", "source", existing_type=sa.String(), nullable=False)
    op.alter_column("jobs", "location", existing_type=sa.String(), nullable=False)
