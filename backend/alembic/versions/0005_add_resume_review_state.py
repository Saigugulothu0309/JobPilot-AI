"""Add persistent resume review state and edited review data.

Revision ID: 0005_add_resume_review_state
Revises: 0004_create_resumes
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0005_add_resume_review_state"
down_revision: Union[str, Sequence[str], None] = "0004_create_resumes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "resumes",
        sa.Column("review_status", sa.String(length=20), nullable=False, server_default="PARSED"),
    )
    op.add_column("resumes", sa.Column("review_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "review_data")
    op.drop_column("resumes", "review_status")