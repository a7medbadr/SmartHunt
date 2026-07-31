"""create scheduler_failed_jobs table

Revision ID: d8e3a1bd9195
Revises: fb5c977f3462
Create Date: 2026-08-01 00:55:00.926392

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d8e3a1bd9195"
down_revision: Union[str, Sequence[str], None] = "fb5c977f3462"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "scheduler_failed_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("job_reference", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scheduler_failed_jobs_job_reference"),
        "scheduler_failed_jobs",
        ["job_reference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduler_failed_jobs_provider"),
        "scheduler_failed_jobs",
        ["provider"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_scheduler_failed_jobs_provider"), table_name="scheduler_failed_jobs")
    op.drop_index(
        op.f("ix_scheduler_failed_jobs_job_reference"), table_name="scheduler_failed_jobs"
    )
    op.drop_table("scheduler_failed_jobs")
