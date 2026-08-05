"""add resume_tailored activity type

Revision ID: ea75465ff425
Revises: 35f1cc8c6d2a
Create Date: 2026-08-03 14:45:55.287444

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ea75465ff425"
down_revision: Union[str, Sequence[str], None] = "35f1cc8c6d2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block on
    # PostgreSQL < 12 (found live 2026-08-04: OpenShift's postgres pod is
    # a very old 10.23 — this crashed the whole pod on startup there,
    # even though it silently worked fine locally against Postgres 17,
    # which relaxed this restriction). autocommit_block() runs this one
    # statement outside Alembic's normal per-migration transaction so it
    # works on both.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE activitytype ADD VALUE IF NOT EXISTS 'RESUME_TAILORED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres has no native DROP VALUE for enum types — removing one
    # safely requires recreating the whole type and repointing the
    # column, which isn't worth doing for a downgrade path. Left as a
    # no-op, matching how enum-value additions are generally handled.
    pass
