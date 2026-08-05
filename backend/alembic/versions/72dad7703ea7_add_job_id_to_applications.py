"""add job_id to applications

Revision ID: 72dad7703ea7
Revises: c5cf26a6abe7
Create Date: 2026-08-03 17:15:46.169554

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "72dad7703ea7"
down_revision: Union[str, Sequence[str], None] = "c5cf26a6abe7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("applications", sa.Column("job_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "applications_job_id_fkey", "applications", "jobs", ["job_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("applications_job_id_fkey", "applications", type_="foreignkey")
    op.drop_column("applications", "job_id")
