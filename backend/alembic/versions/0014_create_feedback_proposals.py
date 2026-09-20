"""Create explicit feedback proposals.

Revision ID: 0014_create_feedback_proposals
Revises: 0013_create_job_feedback
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0014_create_feedback_proposals"
down_revision: Union[str, Sequence[str], None] = "0013_create_job_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Uuid(),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "feedback_id",
            sa.Uuid(),
            sa.ForeignKey("job_feedback.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_field", sa.String(50)),
        sa.Column("previous_value", sa.JSON(), nullable=False),
        sa.Column("proposed_value", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "applied_skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="SET NULL"),
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_feedback_proposals_profile_id", "feedback_proposals", ["profile_id"])
    op.create_index("ix_feedback_proposals_feedback_id", "feedback_proposals", ["feedback_id"])


def downgrade() -> None:
    op.drop_index("ix_feedback_proposals_feedback_id", table_name="feedback_proposals")
    op.drop_index("ix_feedback_proposals_profile_id", table_name="feedback_proposals")
    op.drop_table("feedback_proposals")
