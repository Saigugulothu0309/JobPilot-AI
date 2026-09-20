"""Create private in-app notifications.

Revision ID: 0012_create_notifications
Revises: 0011_create_activity_events
Create Date: 2026-09-07
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0012_create_notifications"
down_revision: Union[str, Sequence[str], None] = "0011_create_activity_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("dedupe_key", sa.String(length=200), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("draft_id", sa.Uuid(), nullable=True),
        sa.Column("application_record_id", sa.Uuid(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_record_id"], ["application_records.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["draft_id"], ["application_drafts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "dedupe_key", name="uq_notifications_key"),
    )
    op.create_index(op.f("ix_notifications_profile_id"), "notifications", ["profile_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_profile_id"), table_name="notifications")
    op.drop_table("notifications")
