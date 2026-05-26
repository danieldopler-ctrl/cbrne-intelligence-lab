from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceCreate(BaseModel):
    name: str
    organization: str
    url: str
    source_type: str = "PUBLIC_DATASET"
    modality: str = "CHEM"
    access_terms: str
    limitations: str


class SourceOut(SourceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: bool
    created_at: datetime


class IngestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: int
    original_filename: str
    sha256: str
    record_count: int
    mapping_version: str
    status: str
    retrieved_at: datetime


class MappingRequest(BaseModel):
    version: str = "v1"
    fields: dict[str, str] = Field(
        description="Normalized field name to source column name mapping."
    )
    hazard_domain: str = "CHEM"
    event_type_default: str = "INCIDENT"
    data_classification: str = "PUBLIC"


class NormalizationResult(BaseModel):
    ingest_batch_id: int
    records_processed: int
    events_created: int
    mapping_version: str


class ConnectorSyncResult(BaseModel):
    source_id: int
    ingest_batch_id: int
    records_received: int
    chemical_events: int
    sha256: str
    mapping_version: str


class BioConnectorSyncResult(BaseModel):
    source_id: int
    ingest_batch_id: int
    records_received: int
    bio_events: int
    duplicate_records: int
    revised_records: int = 0
    non_scorable_records: int = 0
    sha256: str
    mapping_version: str
    limitation: str


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: int
    ingest_batch_id: int
    source_record_id: str
    event_date: str | None
    hazard_domain: str
    event_type: str
    region: str | None
    commodity: str | None
    severity_features: dict[str, Any]
    narrative: str | None
    limitations: str


class DetectionRequest(BaseModel):
    ingest_batch_id: int | None = None
    domain_pack: Literal["CBRNE_CHEM", "CBRNE_BIO", "AI_MISUSE"] = "CBRNE_CHEM"
    include_observations: bool = False


class DetectionResult(BaseModel):
    detection_run_id: int
    events_evaluated: int
    alerts_created: int
    rule_set_version: str


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    priority: str
    result_label: str
    score: int
    confidence: str
    status: str
    recommended_threat_level: str
    confirmed_threat_level: str | None
    review_framework: str
    recommended_review_level: str | None
    confirmed_review_level: str | None
    rationale: str
    created_at: datetime


class AlertDetail(AlertOut):
    evidence: list[dict[str, Any]]
    reviews: list[dict[str, Any]]
    notifications: list[dict[str, Any]]
    plan_reviews: list[dict[str, Any]]


class ReviewCreate(BaseModel):
    reviewer: str
    disposition: Literal[
        "MONITOR",
        "INVESTIGATE",
        "ESCALATE",
        "CLOSED_FALSE_POSITIVE",
        "CLOSED_NO_ACTION",
    ]
    threat_level: Literal["TL0", "TL1", "TL2", "TL3", "TL4"] | None = None
    review_level: Literal["MR0", "MR1", "MR2", "MR3"] | None = None
    note: str


class NotificationCreate(BaseModel):
    threat_level: Literal["TL2", "TL3", "TL4"]
    route_type: Literal["INTERNAL", "EXTERNAL"]
    route_name: str
    reporting_assessment: Literal[
        "NOT_APPLICABLE", "REVIEW_REQUIRED", "REPORTED", "DECLINED_WITH_RATIONALE"
    ]
    authorized_by: str | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    reference_number: str | None = None
    rationale: str


class PlanReviewCreate(BaseModel):
    plan_code: Literal[
        "NIMS_ICS",
        "NRF",
        "ESF_8",
        "ESF_10",
        "NCP_NRS",
        "BIA",
        "NRIA",
        "NARP",
        "PREVENTION_INFO_SHARING",
    ]
    applicability: Literal["POTENTIALLY_APPLICABLE", "NOT_APPLICABLE", "APPLICABLE_VERIFIED"]
    rationale: str
    reviewer: str
    activation_status: Literal["NOT_VERIFIED", "VERIFIED_ACTIVE", "VERIFIED_NOT_ACTIVE"] = (
        "NOT_VERIFIED"
    )
    incident_reference: str | None = None


class EvaluationSetCreate(BaseModel):
    name: str
    version: str
    domain_pack: Literal["CBRNE_CHEM", "AI_MISUSE"]
    review_framework: Literal["THREAT_LEVEL", "AI_MISUSE_REVIEW"]
    evaluation_type: Literal["FIXTURE_CONFORMANCE", "REVIEWED_BENCHMARK"]
    description: str
    source_basis: str
    claim_limit: str
    status: Literal["DRAFT", "READY", "ARCHIVED"] = "DRAFT"


class EvaluationCaseCreate(BaseModel):
    normalized_event_id: int
    case_key: str
    expected_review_level: str
    expected_rule_ids: list[str] = Field(default_factory=list)
    label_rationale: str
    citation: str
    label_status: Literal["ANALYST_REVIEWED", "DRAFT"] = "ANALYST_REVIEWED"


class EvaluationRunCreate(BaseModel):
    evaluation_set_id: int
    detection_run_id: int
