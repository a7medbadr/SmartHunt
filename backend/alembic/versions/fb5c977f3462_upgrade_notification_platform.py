"""upgrade notification platform

Revision ID: fb5c977f3462
Revises: cf4efd1e3985
Create Date: 2026-07-30

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "fb5c977f3462"
down_revision: Union[str, Sequence[str], None] = "cf4efd1e3985"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "notifications",
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "notifications",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
    )

    op.add_column(
        "notifications",
        sa.Column(
            "channel",
            sa.String(length=20),
            nullable=False,
            server_default="IN_APP",
        ),
    )

    op.add_column(
        "notifications",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="NORMAL",
        ),
    )

    op.add_column(
        "notifications",
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "notifications",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_notifications_user_id",
        "notifications",
        ["user_id"],
    )

    op.create_index(
        "ix_notifications_type",
        "notifications",
        ["type"],
    )

    op.create_index(
        "ix_notifications_status",
        "notifications",
        ["status"],
    )

    op.create_index(
        "ix_notifications_channel",
        "notifications",
        ["channel"],
    )

    op.create_index(
        "ix_notifications_priority",
        "notifications",
        ["priority"],
    )

    op.create_index(
        "ix_notifications_created_at",
        "notifications",
        ["created_at"],
    )

    op.create_index(
        "ix_notifications_expires_at",
        "notifications",
        ["expires_at"],
    )

    op.create_foreign_key(
        "fk_notifications_user",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_column(
        "notifications",
        "is_read",
    )

    op.alter_column(
        "notifications",
        "status",
        server_default=None,
    )

    op.alter_column(
        "notifications",
        "channel",
        server_default=None,
    )

    op.alter_column(
        "notifications",
        "priority",
        server_default=None,
    )


def downgrade() -> None:

    op.add_column(
        "notifications",
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.drop_constraint(
        "fk_notifications_user",
        "notifications",
        type_="foreignkey",
    )

    op.drop_index("ix_notifications_expires_at", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_priority", table_name="notifications")
    op.drop_index("ix_notifications_channel", table_name="notifications")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")

    op.drop_column("notifications", "expires_at")
    op.drop_column("notifications", "read_at")
    op.drop_column("notifications", "priority")
    op.drop_column("notifications", "channel")
    op.drop_column("notifications", "status")
    op.drop_column("notifications", "user_id")

    op.alter_column(
        "notifications",
        "is_read",
        server_default=None,
    )
