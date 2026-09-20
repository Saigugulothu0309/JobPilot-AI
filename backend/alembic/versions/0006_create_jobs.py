"""Create normalized shared jobs table.

Revision ID: 0006_create_jobs
Revises: 0005_add_resume_review_state
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0006_create_jobs"
down_revision: Union[str, Sequence[str], None] = "0005_add_resume_review_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("company", sa.String(length=300), nullable=False),
        sa.Column("location", sa.String(length=300), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("employment_type", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("external_job_id", sa.String(length=300), nullable=True),
        sa.Column("external_url", sa.String(length=2048), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dedupe_key", sa.String(length=512), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key", name="uq_jobs_dedupe_key"),
    )
    op.create_index(op.f("ix_jobs_source"), "jobs", ["source"], unique=False)
    op.create_index(op.f("ix_jobs_external_job_id"), "jobs", ["external_job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_external_job_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_source"), table_name="jobs")
    op.drop_table("jobs")