"""drop saved_searches table

Revision ID: 2c1684253667
Revises: 72369e67d276
Create Date: 2026-08-06 05:32:09.973970

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2c1684253667"
down_revision: Union[str, Sequence[str], None] = "72369e67d276"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("saved_searches")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("keyword", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("location", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("saved_searches_pkey")),
    )
