"""Add explicit application draft approval state.

Revision ID: 0009_add_application_draft_approval
Revises: 0008_create_application_drafts
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0009_add_application_draft_approval"
down_revision: Union[str, Sequence[str], None] = "0008_create_application_drafts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "application_drafts",
        sa.Column("approved_revision", sa.Integer(), nullable=True),
    )
    op.add_column(
        "application_drafts",
        sa.Column("approval_confirmed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("application_drafts", "approval_confirmed")
    op.drop_column("application_drafts", "approved_revision")
