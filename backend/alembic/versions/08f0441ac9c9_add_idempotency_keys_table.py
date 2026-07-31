"""add idempotency keys table

Revision ID: 08f0441ac9c9
Revises: 6a8d7c4b9f21
Create Date: 2026-07-20 23:25:27.885774

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "08f0441ac9c9"
down_revision: Union[str, Sequence[str], None] = "6a8d7c4b9f21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column(
            "key",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "response",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
