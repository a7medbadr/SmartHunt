"""add unknown_questions table

Revision ID: 35f1cc8c6d2a
Revises: 614cc7665af0
Create Date: 2026-08-03 14:23:42.276820

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "35f1cc8c6d2a"
down_revision: Union[str, Sequence[str], None] = "614cc7665af0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "unknown_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("html", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_unknown_questions_provider"), "unknown_questions", ["provider"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_unknown_questions_provider"), table_name="unknown_questions")
    op.drop_table("unknown_questions")
