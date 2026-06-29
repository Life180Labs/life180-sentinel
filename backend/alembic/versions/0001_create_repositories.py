"""create repositories table

Revision ID: 0001
Revises:
Create Date: 2026-06-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(512), nullable=False, unique=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("default_branch", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("local_path", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("repositories")
