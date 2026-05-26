"""Add evaluation and backtesting framework tables.

Revision ID: 0004_add_evaluation_framework
Revises: 0003_add_review_framework
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_add_evaluation_framework"
down_revision = "0003_add_review_framework"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_sets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("domain_pack", sa.String(length=50), nullable=False),
        sa.Column("review_framework", sa.String(length=30), nullable=False),
        sa.Column("evaluation_type", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_basis", sa.Text(), nullable=False),
        sa.Column("claim_limit", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "evaluation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evaluation_set_id", sa.Integer(), sa.ForeignKey("evaluation_sets.id"), nullable=False),
        sa.Column("case_key", sa.String(length=100), nullable=False),
        sa.Column("normalized_event_id", sa.Integer(), sa.ForeignKey("normalized_events.id"), nullable=True),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("expected_review_level", sa.String(length=10), nullable=False),
        sa.Column("expected_rule_ids", sa.JSON(), nullable=False),
        sa.Column("label_rationale", sa.Text(), nullable=False),
        sa.Column("citation", sa.Text(), nullable=True),
        sa.Column("label_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("evaluation_set_id", "case_key", name="uq_evaluation_case_key"),
    )
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evaluation_set_id", sa.Integer(), sa.ForeignKey("evaluation_sets.id"), nullable=False),
        sa.Column("detection_run_id", sa.Integer(), sa.ForeignKey("detection_runs.id"), nullable=False),
        sa.Column("rule_set_version", sa.String(length=30), nullable=False),
        sa.Column("evaluation_type", sa.String(length=40), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("evaluation_set_id", "detection_run_id", name="uq_evaluation_set_detection_run"),
    )
    op.create_table(
        "evaluation_case_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evaluation_run_id", sa.Integer(), sa.ForeignKey("evaluation_runs.id"), nullable=False),
        sa.Column("evaluation_case_id", sa.Integer(), sa.ForeignKey("evaluation_cases.id"), nullable=False),
        sa.Column("generated_review_level", sa.String(length=10), nullable=False),
        sa.Column("generated_rule_ids", sa.JSON(), nullable=False),
        sa.Column("alert_ids", sa.JSON(), nullable=False),
        sa.Column("result", sa.String(length=40), nullable=False),
        sa.Column("result_rationale", sa.Text(), nullable=False),
        sa.UniqueConstraint("evaluation_run_id", "evaluation_case_id", name="uq_evaluation_result_case"),
    )


def downgrade() -> None:
    op.drop_table("evaluation_case_results")
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_cases")
    op.drop_table("evaluation_sets")
