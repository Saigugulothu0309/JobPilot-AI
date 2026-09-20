"""Create professional candidate data tables.

Revision ID: 0003_create_professional_data
Revises: 0002_create_profiles
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_create_professional_data"
down_revision: Union[str, Sequence[str], None] = "0002_create_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("proficiency", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "name", name="uq_skills_profile_name"),
    )
    op.create_index(op.f("ix_skills_profile_id"), "skills", ["profile_id"], unique=False)

    op.create_table(
        "education",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("institution", sa.String(length=200), nullable=False),
        sa.Column("degree", sa.String(length=150), nullable=True),
        sa.Column("field_of_study", sa.String(length=200), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_education_profile_id"), "education", ["profile_id"], unique=False)

    op.create_table(
        "experience",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("job_title", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_experience_profile_id"), "experience", ["profile_id"], unique=False)

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_profile_id"), "projects", ["profile_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_profile_id"), table_name="projects")
    op.drop_index(op.f("ix_experience_profile_id"), table_name="experience")
    op.drop_index(op.f("ix_education_profile_id"), table_name="education")
    op.drop_index(op.f("ix_skills_profile_id"), table_name="skills")
    op.drop_table("projects")
    op.drop_table("experience")
    op.drop_table("education")
    op.drop_table("skills")
