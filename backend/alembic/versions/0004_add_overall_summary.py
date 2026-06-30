"""add overall_summary to repositories

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("overall_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("repositories", "overall_summary")
