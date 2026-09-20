"""Create owner-scoped one-time job feedback.

Revision ID: 0013_create_job_feedback
Revises: 0012_create_notifications
Create Date: 2026-09-07
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0013_create_job_feedback"
down_revision: Union[str, Sequence[str], None] = "0012_create_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("feedback_type", sa.String(length=50), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id", "job_id", "feedback_type", name="uq_job_feedback_signal"
        ),
    )
    op.create_index(op.f("ix_job_feedback_job_id"), "job_feedback", ["job_id"], unique=False)
    op.create_index(
        op.f("ix_job_feedback_profile_id"), "job_feedback", ["profile_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_job_feedback_profile_id"), table_name="job_feedback")
    op.drop_index(op.f("ix_job_feedback_job_id"), table_name="job_feedback")
    op.drop_table("job_feedback")
