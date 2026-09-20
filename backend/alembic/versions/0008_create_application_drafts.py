"""Create grounded application preparation drafts.

Revision ID: 0008_create_application_drafts
Revises: 0007_create_career_preferences
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0008_create_application_drafts"
down_revision: Union[str, Sequence[str], None] = "0007_create_career_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_drafts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="DRAFT", nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("profile_snapshot", sa.JSON(), nullable=False),
        sa.Column("job_snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "job_id", name="uq_application_drafts_profile_job"),
    )
    op.create_index(
        op.f("ix_application_drafts_profile_id"),
        "application_drafts",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_drafts_job_id"),
        "application_drafts",
        ["job_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_application_drafts_job_id"), table_name="application_drafts")
    op.drop_index(op.f("ix_application_drafts_profile_id"), table_name="application_drafts")
    op.drop_table("application_drafts")
