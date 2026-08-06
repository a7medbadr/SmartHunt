"""add monitored_hashtags table, seed owner's existing hashtag list

Revision ID: e25fa514e5a8
Revises: 2c1684253667
Create Date: 2026-08-06 06:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e25fa514e5a8"
down_revision: Union[str, Sequence[str], None] = "2c1684253667"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The owner's own hashtag list (2026-08-05), moving here from
# scheduler/jobs.py's old hardcoded HASHTAG_LIST — one-time seed data for
# a table the owner now manages directly from the job-search page.
_SEED_HASHTAGS = [
    "Hiring",
    "HiringNow",
    "HiringAlert",
    "SaudiJobs",
    "SaudiArabia",
    "SaudiArabiaJobs",
    "KSAJobs",
    "RiyadhJobs",
    "ITJobs",
    "TechJobs",
    "Infrastructure",
    "InfrastructureLead",
    "ITSupport",
    "FieldSupport",
    "DesktopSupport",
    "SystemAdministration",
    "Cloud",
    "CloudInfrastructure",
    "Networking",
    "OnsiteJobs",
    "Recruitment",
    "CareerOpportunities",
    "JoinUs",
    "Linux",
    "RHEL",
    "RHCE",
    "Ansible",
    "Terraform",
    "Kubernetes",
    "CKA",
    "DevOps",
    "Automation",
]


def upgrade() -> None:
    """Upgrade schema."""
    monitored_hashtags = op.create_table(
        "monitored_hashtags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tag"),
    )

    op.bulk_insert(
        monitored_hashtags,
        [{"tag": tag, "enabled": True} for tag in _SEED_HASHTAGS],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("monitored_hashtags")
