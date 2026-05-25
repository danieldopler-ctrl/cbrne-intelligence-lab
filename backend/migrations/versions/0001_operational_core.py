"""Create operational risk signal platform core tables.

Revision ID: 0001_operational_core
Revises:
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_operational_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("organization", sa.String(length=200), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("modality", sa.String(length=50), nullable=False),
        sa.Column("access_terms", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "ingest_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("mapping_version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
    )
    op.create_table(
        "raw_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ingest_batch_id", sa.Integer(), sa.ForeignKey("ingest_batches.id"), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("raw_hash", sa.String(length=64), nullable=False),
    )
    op.create_table(
        "normalized_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("ingest_batch_id", sa.Integer(), sa.ForeignKey("ingest_batches.id"), nullable=False),
        sa.Column("raw_record_id", sa.Integer(), sa.ForeignKey("raw_records.id"), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("event_date", sa.String(length=40)),
        sa.Column("reported_date", sa.String(length=40)),
        sa.Column("hazard_domain", sa.String(length=20), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=200)),
        sa.Column("severity_features", sa.JSON(), nullable=False),
        sa.Column("narrative", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("data_classification", sa.String(length=30), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "detection_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain_pack", sa.String(length=50), nullable=False),
        sa.Column("rule_id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("logic_config", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "detection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ingest_batch_id", sa.Integer(), sa.ForeignKey("ingest_batches.id")),
        sa.Column("domain_pack", sa.String(length=50), nullable=False),
        sa.Column("rule_set_version", sa.String(length=30), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("alert_count", sa.Integer(), nullable=False),
    )
    op.create_table(
        "indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("normalized_events.id"), nullable=False),
        sa.Column("detection_run_id", sa.Integer(), sa.ForeignKey("detection_runs.id"), nullable=False),
        sa.Column("detection_rule_id", sa.Integer(), sa.ForeignKey("detection_rules.id"), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("indicator_score", sa.Integer(), nullable=False),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("detection_run_id", sa.Integer(), sa.ForeignKey("detection_runs.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.String(length=30), nullable=False),
        sa.Column("result_label", sa.String(length=40), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("recommended_threat_level", sa.String(length=10), nullable=False),
        sa.Column("confirmed_threat_level", sa.String(length=10)),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "alert_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("normalized_events.id"), nullable=False),
        sa.Column("indicator_id", sa.Integer(), sa.ForeignKey("indicators.id"), nullable=False),
    )
    op.create_table(
        "analyst_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("reviewer", sa.String(length=100), nullable=False),
        sa.Column("disposition", sa.String(length=50), nullable=False),
        sa.Column("threat_level", sa.String(length=10), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "notification_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("threat_level", sa.String(length=10), nullable=False),
        sa.Column("route_type", sa.String(length=30), nullable=False),
        sa.Column("route_name", sa.String(length=150), nullable=False),
        sa.Column("reporting_assessment", sa.String(length=50), nullable=False),
        sa.Column("authorized_by", sa.String(length=100)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("reference_number", sa.String(length=100)),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "plan_applicability_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("plan_code", sa.String(length=50), nullable=False),
        sa.Column("applicability", sa.String(length=50), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("reviewer", sa.String(length=100), nullable=False),
        sa.Column("activation_status", sa.String(length=50), nullable=False),
        sa.Column("incident_reference", sa.String(length=200)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("object_id", sa.String(length=100), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table_name in [
        "audit_events",
        "plan_applicability_reviews",
        "notification_actions",
        "analyst_reviews",
        "alert_evidence",
        "alerts",
        "indicators",
        "detection_runs",
        "detection_rules",
        "normalized_events",
        "raw_records",
        "ingest_batches",
        "sources",
    ]:
        op.drop_table(table_name)
