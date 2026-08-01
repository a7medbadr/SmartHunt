"""fix resumes table schema drift

The e2fdd783e4aa migration that created `resumes` was edited in place
after already being applied to at least one real database (this one) —
its checked-in version has created_at/updated_at and a nullable
extracted_text, but the actual deployed table has neither: no
created_at/updated_at columns at all, and extracted_text is NOT NULL.
Alembic never caught this because the revision ID never changed, so it
never re-ran. Went unnoticed for months because nothing ever actually
queried/wrote to `resumes` — the Resume model + ResumeRepository were
fully built but orphaned until resume upload was wired to persist to
the DB (2026-08-01), at which point every upload started failing with
`UndefinedColumnError: column resumes.created_at does not exist`.

Revision ID: 614cc7665af0
Revises: 44880b2539e9
Create Date: 2026-08-01 14:13:15.312212

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "614cc7665af0"
down_revision: Union[str, Sequence[str], None] = "44880b2539e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Uses IF NOT EXISTS / is idempotent throughout: a freshly-created
    database (test DB, CI, a new deployment) runs the *current*,
    already-correct e2fdd783e4aa migration and won't be missing these
    columns at all — this migration only needs to do real work against
    a database that had the old, pre-fix version of that migration
    applied to it before it was edited in place.
    """
    op.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP")
    op.execute("UPDATE resumes SET created_at = now() WHERE created_at IS NULL")
    op.execute("ALTER TABLE resumes ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE resumes ALTER COLUMN created_at SET NOT NULL")

    op.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP")
    op.execute("UPDATE resumes SET updated_at = now() WHERE updated_at IS NULL")
    op.execute("ALTER TABLE resumes ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE resumes ALTER COLUMN updated_at SET NOT NULL")

    op.alter_column("resumes", "extracted_text", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("resumes", "extracted_text", existing_type=sa.Text(), nullable=False)
    op.drop_column("resumes", "updated_at")
    op.drop_column("resumes", "created_at")
