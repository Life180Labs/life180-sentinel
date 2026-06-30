"""add eval_run, reasoning, confidence, recommendation_scores

Adds version history (eval_run) to repositories and evaluations,
plus richer per-category fields: reasoning, confidence, recommendation_scores.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("eval_run", sa.Integer(), nullable=False, server_default="1"))

    op.add_column("evaluations", sa.Column("eval_run", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("evaluations", sa.Column("reasoning", sa.Text(), nullable=True))
    op.add_column("evaluations", sa.Column("confidence", sa.Integer(), nullable=True))
    op.add_column("evaluations", sa.Column("recommendation_scores", JSON(), nullable=True))
    op.create_index("ix_evaluations_repo_run", "evaluations", ["repository_id", "eval_run"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_repo_run", table_name="evaluations")
    op.drop_column("evaluations", "recommendation_scores")
    op.drop_column("evaluations", "confidence")
    op.drop_column("evaluations", "reasoning")
    op.drop_column("evaluations", "eval_run")
    op.drop_column("repositories", "eval_run")
