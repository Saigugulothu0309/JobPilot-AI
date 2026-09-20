"""Create manual application tracking records.

Revision ID: 0010_create_application_records
Revises: 0009_add_application_draft_approval
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0010_create_application_records"
down_revision: Union[str, Sequence[str], None] = "0009_add_application_draft_approval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("draft_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="SAVED", nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column(
            "saved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interview_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("draft_revision", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["draft_id"], ["application_drafts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "job_id", name="uq_application_records_profile_job"),
    )
    op.create_index(
        op.f("ix_application_records_profile_id"),
        "application_records",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_records_job_id"),
        "application_records",
        ["job_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_application_records_job_id"), table_name="application_records")
    op.drop_index(op.f("ix_application_records_profile_id"), table_name="application_records")
    op.drop_table("application_records")