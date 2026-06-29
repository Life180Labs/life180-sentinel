"""create evaluations table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("findings", JSON, nullable=False, server_default="[]"),
        sa.Column("recommendations", JSON, nullable=False, server_default="[]"),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("raw_response", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evaluations")
