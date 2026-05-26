from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    organization: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50))
    modality: Mapped[str] = mapped_column(String(50))
    access_terms: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestBatch(Base):
    __tablename__ = "ingest_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    mapping_version: Mapped[str] = mapped_column(String(50), default="unmapped")
    status: Mapped[str] = mapped_column(String(30), default="UPLOADED")
    source: Mapped[Source] = relationship()


class RawRecord(Base):
    __tablename__ = "raw_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingest_batch_id: Mapped[int] = mapped_column(ForeignKey("ingest_batches.id"))
    source_record_id: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSON)
    raw_hash: Mapped[str] = mapped_column(String(64))


class NormalizedEvent(Base):
    __tablename__ = "normalized_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    ingest_batch_id: Mapped[int] = mapped_column(ForeignKey("ingest_batches.id"))
    raw_record_id: Mapped[int] = mapped_column(ForeignKey("raw_records.id"))
    source_record_id: Mapped[str] = mapped_column(String(255))
    event_date: Mapped[str | None] = mapped_column(String(40))
    reported_date: Mapped[str | None] = mapped_column(String(40))
    hazard_domain: Mapped[str] = mapped_column(String(20))
    event_type: Mapped[str] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(200))
    commodity: Mapped[str | None] = mapped_column(String(255))
    severity_features: Mapped[dict] = mapped_column(JSON, default=dict)
    narrative: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    data_classification: Mapped[str] = mapped_column(String(30), default="PUBLIC")
    limitations: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain_pack: Mapped[str] = mapped_column(String(50))
    rule_id: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    rationale: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(30))
    logic_config: Mapped[dict] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class DetectionRun(Base):
    __tablename__ = "detection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingest_batch_id: Mapped[int | None] = mapped_column(ForeignKey("ingest_batches.id"))
    domain_pack: Mapped[str] = mapped_column(String(50))
    rule_set_version: Mapped[str] = mapped_column(String(30))
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    alert_count: Mapped[int] = mapped_column(Integer, default=0)


class EvaluationSet(Base):
    __tablename__ = "evaluation_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(50))
    domain_pack: Mapped[str] = mapped_column(String(50))
    review_framework: Mapped[str] = mapped_column(String(30))
    evaluation_type: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    source_basis: Mapped[str] = mapped_column(Text)
    claim_limit: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_set_id: Mapped[int] = mapped_column(ForeignKey("evaluation_sets.id"))
    case_key: Mapped[str] = mapped_column(String(100))
    normalized_event_id: Mapped[int | None] = mapped_column(ForeignKey("normalized_events.id"))
    source_record_id: Mapped[str] = mapped_column(String(255))
    expected_review_level: Mapped[str] = mapped_column(String(10))
    expected_rule_ids: Mapped[list] = mapped_column(JSON, default=list)
    label_rationale: Mapped[str] = mapped_column(Text)
    citation: Mapped[str | None] = mapped_column(Text)
    label_status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_set_id: Mapped[int] = mapped_column(ForeignKey("evaluation_sets.id"))
    detection_run_id: Mapped[int] = mapped_column(ForeignKey("detection_runs.id"))
    rule_set_version: Mapped[str] = mapped_column(String(30))
    evaluation_type: Mapped[str] = mapped_column(String(40))
    case_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvaluationCaseResult(Base):
    __tablename__ = "evaluation_case_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id"))
    evaluation_case_id: Mapped[int] = mapped_column(ForeignKey("evaluation_cases.id"))
    generated_review_level: Mapped[str] = mapped_column(String(10))
    generated_rule_ids: Mapped[list] = mapped_column(JSON, default=list)
    alert_ids: Mapped[list] = mapped_column(JSON, default=list)
    result: Mapped[str] = mapped_column(String(40))
    result_rationale: Mapped[str] = mapped_column(Text)


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("normalized_events.id"))
    detection_run_id: Mapped[int] = mapped_column(ForeignKey("detection_runs.id"))
    detection_rule_id: Mapped[int] = mapped_column(ForeignKey("detection_rules.id"))
    evidence: Mapped[dict] = mapped_column(JSON)
    indicator_score: Mapped[int] = mapped_column(Integer)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    detection_run_id: Mapped[int] = mapped_column(ForeignKey("detection_runs.id"))
    title: Mapped[str] = mapped_column(String(255))
    priority: Mapped[str] = mapped_column(String(30))
    result_label: Mapped[str] = mapped_column(String(40))
    score: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(40), default="NEW")
    recommended_threat_level: Mapped[str] = mapped_column(String(10), default="TL1")
    confirmed_threat_level: Mapped[str | None] = mapped_column(String(10))
    review_framework: Mapped[str] = mapped_column(String(30), default="THREAT_LEVEL")
    recommended_review_level: Mapped[str | None] = mapped_column(String(10))
    confirmed_review_level: Mapped[str | None] = mapped_column(String(10))
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertEvidence(Base):
    __tablename__ = "alert_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("normalized_events.id"))
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicators.id"))


class AnalystReview(Base):
    __tablename__ = "analyst_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"))
    reviewer: Mapped[str] = mapped_column(String(100))
    disposition: Mapped[str] = mapped_column(String(50))
    threat_level: Mapped[str] = mapped_column(String(10))
    review_framework: Mapped[str] = mapped_column(String(30), default="THREAT_LEVEL")
    review_level: Mapped[str | None] = mapped_column(String(10))
    note: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationAction(Base):
    __tablename__ = "notification_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"))
    threat_level: Mapped[str] = mapped_column(String(10))
    route_type: Mapped[str] = mapped_column(String(30))
    route_name: Mapped[str] = mapped_column(String(150))
    reporting_assessment: Mapped[str] = mapped_column(String(50))
    authorized_by: Mapped[str | None] = mapped_column(String(100))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_number: Mapped[str | None] = mapped_column(String(100))
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlanApplicabilityReview(Base):
    __tablename__ = "plan_applicability_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"))
    plan_code: Mapped[str] = mapped_column(String(50))
    applicability: Mapped[str] = mapped_column(String(50))
    rationale: Mapped[str] = mapped_column(Text)
    reviewer: Mapped[str] = mapped_column(String(100))
    activation_status: Mapped[str] = mapped_column(String(50), default="NOT_VERIFIED")
    incident_reference: Mapped[str | None] = mapped_column(String(200))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100))
    object_type: Mapped[str] = mapped_column(String(100))
    object_id: Mapped[str] = mapped_column(String(100))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
