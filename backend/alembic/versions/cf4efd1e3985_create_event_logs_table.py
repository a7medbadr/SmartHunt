"""create event logs table

Revision ID: cf4efd1e3985
Revises: fdf369cfdd06
Create Date: 2026-07-30 23:09:52.109237

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "cf4efd1e3985"
down_revision: Union[str, Sequence[str], None] = "fdf369cfdd06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_logs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "payload",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_event_logs_created_at",
        "event_logs",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_event_logs_event_type",
        "event_logs",
        ["event_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_logs_event_type",
        table_name="event_logs",
    )

    op.drop_index(
        "ix_event_logs_created_at",
        table_name="event_logs",
    )

    op.drop_table("event_logs")
