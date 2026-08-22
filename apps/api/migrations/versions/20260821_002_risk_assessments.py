"""Create model-version and risk-assessment audit tables.

Revision ID: 20260821_002
Revises: 20260821_001
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260821_002"
down_revision: str | None = "20260821_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("algorithm", sa.String(length=80), nullable=False),
        sa.Column("feature_names", sa.JSON(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
    )
    op.create_index("ix_model_versions_name", "model_versions", ["name"], unique=False)
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transaction_id", sa.String(length=36), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("ml_probability", sa.Float(), nullable=False),
        sa.Column("rules_score", sa.Float(), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=40), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("feature_values", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("transaction_id", "risk_score", "decision"):
        op.create_index(f"ix_risk_assessments_{column}", "risk_assessments", [column], unique=False)


def downgrade() -> None:
    op.drop_table("risk_assessments")
    op.drop_table("model_versions")
