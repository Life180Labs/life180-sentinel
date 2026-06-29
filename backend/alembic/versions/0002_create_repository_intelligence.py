"""create repository_intelligence table

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repository_intelligence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("languages", JSON, nullable=False, server_default="[]"),
        sa.Column("frameworks", JSON, nullable=False, server_default="[]"),
        sa.Column("package_managers", JSON, nullable=False, server_default="[]"),
        sa.Column("databases", JSON, nullable=False, server_default="[]"),
        sa.Column("docker", JSON, nullable=False, server_default="[]"),
        sa.Column("cicd", JSON, nullable=False, server_default="[]"),
        sa.Column("ai_frameworks", JSON, nullable=False, server_default="[]"),
        sa.Column("file_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("folder_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tree", JSON, nullable=False, server_default="{}"),
        sa.Column("tree_text", sa.Text, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("repository_intelligence")
