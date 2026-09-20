"""Create user-visible activity events.

Revision ID: 0011_create_activity_events
Revises: 0010_create_application_records
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0011_create_activity_events"
down_revision: Union[str, Sequence[str], None] = "0010_create_application_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activity_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("draft_id", sa.Uuid(), nullable=True),
        sa.Column("application_record_id", sa.Uuid(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_record_id"], ["application_records.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["draft_id"], ["application_drafts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_activity_events_profile_id"),
        "activity_events",
        ["profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_events_profile_id"), table_name="activity_events")
    op.drop_table("activity_events")
