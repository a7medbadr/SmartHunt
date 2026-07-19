"""create dashboard tables

Revision ID: create_dashboard_tables
Revises: a1f9c3d7e2b4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "create_dashboard_tables"
down_revision = "a1f9c3d7e2b4"
branch_labels = None
depends_on = None


activity_type = sa.Enum(
    "RESUME_UPLOADED",
    "APPLICATION_CREATED",
    "FAVORITE_ADDED",
    "SAVED_SEARCH_CREATED",
    "COVER_LETTER_GENERATED",
    name="activitytype",
    create_type=False,
)


def upgrade():

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", activity_type, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("details", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_activities_id",
        "activities",
        ["id"],
    )

    op.create_index(
        "ix_activities_created_at",
        "activities",
        ["created_at"],
    )

    op.create_table(
        "favorite_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String()),
        sa.Column("source", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_index(
        "ix_favorite_jobs_id",
        "favorite_jobs",
        ["id"],
    )

    op.create_index(
        "ix_favorite_jobs_job_id",
        "favorite_jobs",
        ["job_id"],
        unique=True,
    )

    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("keyword", sa.String()),
        sa.Column("location", sa.String()),
        sa.Column("source", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_index(
        "ix_saved_searches_id",
        "saved_searches",
        ["id"],
    )


def downgrade():

    op.drop_index("ix_saved_searches_id", table_name="saved_searches")
    op.drop_table("saved_searches")

    op.drop_index("ix_favorite_jobs_job_id", table_name="favorite_jobs")
    op.drop_index("ix_favorite_jobs_id", table_name="favorite_jobs")
    op.drop_table("favorite_jobs")

    op.drop_index("ix_activities_created_at", table_name="activities")
    op.drop_index("ix_activities_id", table_name="activities")
    op.drop_table("activities")
