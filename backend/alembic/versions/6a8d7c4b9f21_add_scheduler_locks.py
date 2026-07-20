"""add scheduler locks

Revision ID: 6a8d7c4b9f21
Revises: af224e44b10d
Create Date: 2026-07-30

"""

from alembic import op
import sqlalchemy as sa

revision = "6a8d7c4b9f21"
down_revision = "af224e44b10d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_locks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=255), nullable=False),
        sa.Column("owner_id", sa.String(length=255), nullable=False),
        sa.Column("acquired_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_scheduler_locks_job_id",
        "scheduler_locks",
        ["job_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scheduler_locks_job_id",
        table_name="scheduler_locks",
    )

    op.drop_table("scheduler_locks")
