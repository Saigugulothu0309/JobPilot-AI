"""Create resumes table.

Revision ID: 0004_create_resumes
Revises: 0003_create_professional_data
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_create_resumes"
down_revision: Union[str, Sequence[str], None] = "0003_create_professional_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resumes_profile_id"), "resumes", ["profile_id"], unique=False)
    op.create_index(op.f("ix_resumes_storage_key"), "resumes", ["storage_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_resumes_storage_key"), table_name="resumes")
    op.drop_index(op.f("ix_resumes_profile_id"), table_name="resumes")
    op.drop_table("resumes")
