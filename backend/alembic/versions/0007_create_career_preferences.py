"""Create user-owned career preferences.

Revision ID: 0007_create_career_preferences
Revises: 0006_create_jobs
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0007_create_career_preferences"
down_revision: Union[str, Sequence[str], None] = "0006_create_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    empty_json = sa.text("'[]'")
    op.create_table(
        "career_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("target_roles", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("employment_types", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("locations", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("work_modes", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("industries", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("technologies", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("career_interests", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("exclusions", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("hard_constraints", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("ranking_preferences", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("optional_preferences", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column("deal_breakers", sa.JSON(), server_default=empty_json, nullable=False),
        sa.Column(
            "relocation_preference",
            sa.String(length=20),
            server_default="NOT_SPECIFIED",
            nullable=False,
        ),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("available_from", sa.Date(), nullable=True),
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
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", name="uq_career_preferences_profile_id"),
    )


def downgrade() -> None:
    op.drop_table("career_preferences")