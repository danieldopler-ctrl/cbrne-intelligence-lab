"""Add source-cited report storage.

Revision ID: 0005_add_reports
Revises: 0004_add_evaluation_framework
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_add_reports"
down_revision = "0004_add_evaluation_framework"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain_pack", sa.String(length=50), nullable=False),
        sa.Column("rule_set_version", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("alert_ids", sa.JSON(), nullable=False),
        sa.Column("report_data", sa.JSON(), nullable=False),
        sa.Column("claim_summary", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reports")
