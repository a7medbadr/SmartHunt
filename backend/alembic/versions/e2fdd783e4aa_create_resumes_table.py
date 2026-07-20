"""create resumes table

Revision ID: e2fdd783e4aa
Revises: b8d5d9f1d8a9
Create Date: 2026-07-16 11:25:13.977187

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2fdd783e4aa"
down_revision: Union[str, Sequence[str], None] = "b8d5d9f1d8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "resumes",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "filename",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "stored_path",
            sa.String(length=512),
            nullable=False,
        ),

        sa.Column(
            "extracted_text",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )


def downgrade() -> None:

    op.drop_table(
        "resumes"
    )
