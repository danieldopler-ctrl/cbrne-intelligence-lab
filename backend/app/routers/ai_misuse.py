import json
from collections import Counter, defaultdict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.config import settings
from app.database import get_db
from app.ingestion.delimited_upload import hash_bytes, raw_record_hash, store_raw_file
from app.models import (
    Alert,
    AlertEvidence,
    DetectionRule,
    DetectionRun,
    Indicator,
    IngestBatch,
    NormalizedEvent,
    RawRecord,
    Source,
)
from app.schemas.api import ConnectorSyncResult


router = APIRouter(prefix="/ai-misuse", tags=["ai-misuse"])

SOURCE_NAME = "AI Misuse Safe Evaluation Set V0.1"
FIXTURE_VERSION = "AI_MISUSE_SAFE_EVAL_V0.1"
FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "ai_misuse" / "ai_misuse_safe_eval_v0.1.json"
LIMITATIONS = (
    "Synthetic, abstract workflow-evaluation record only. It is not a real user interaction, "
    "model completion, threat incident, or evidence of malicious intent. It contains no "
    "operational hazardous-material instructions and does not support external reporting."
)


def _source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == SOURCE_NAME))
    if source:
        return source
    source = Source(
        name=SOURCE_NAME,
        organization="CBRN-E Intelligence Lab controlled fixture",
        url="https://doi.org/10.6028/NIST.AI.600-1",
        source_type="SYNTHETIC_TEST",
        modality="AI_MISUSE",
        access_terms="Repository-owned abstract test cases safe for public workflow demonstration.",
        limitations=LIMITATIONS,
    )
    db.add(source)
    db.flush()
    record_audit(db, "SOURCE_REGISTERED", "source", source.id, actor="ai_misuse_fixture")
    return source


@router.post("/import-safe-evaluation", response_model=ConnectorSyncResult, status_code=201)
def import_safe_evaluation(db: Session = Depends(get_db)) -> ConnectorSyncResult:
    content = FIXTURE_PATH.read_bytes()
    records = json.loads(content)
    source = _source(db)
    stored_path = store_raw_file(settings.data_dir / "raw", FIXTURE_PATH.name, content)
    batch = IngestBatch(
        source_id=source.id,
        original_filename=FIXTURE_PATH.name,
        stored_path=str(stored_path),
        sha256=hash_bytes(content),
        record_count=len(records),
        mapping_version="ai-misuse-safe-eval-v0.1",
        status="NORMALIZED",
    )
    db.add(batch)
    db.flush()
    for record in records:
        case_id = str(record["case_id"])
        raw = RawRecord(
            ingest_batch_id=batch.id,
            source_record_id=case_id,
            payload=record,
            raw_hash=raw_record_hash(record),
        )
        db.add(raw)
        db.flush()
        features = {key: value for key, value in record.items() if key not in {"case_id", "summary"}}
        features["case_version"] = FIXTURE_VERSION
        db.add(
            NormalizedEvent(
                source_id=source.id,
                ingest_batch_id=batch.id,
                raw_record_id=raw.id,
                source_record_id=case_id,
                event_date=None,
                reported_date=None,
                hazard_domain="AI_MISUSE",
                event_type="MISUSE_ASSESSMENT_CASE",
                region=None,
                commodity=None,
                severity_features=features,
                narrative=record["summary"],
                source_url=source.url,
                data_classification="SYNTHETIC_TEST",
                limitations=LIMITATIONS,
            )
        )
    record_audit(
        db,
        "SAFE_EVALUATION_IMPORTED",
        "ingest_batch",
        batch.id,
        actor="ai_misuse_fixture",
        metadata={"evaluation_set": FIXTURE_VERSION, "cases": len(records)},
    )
    db.commit()
    return ConnectorSyncResult(
        source_id=source.id,
        ingest_batch_id=batch.id,
        records_received=len(records),
        chemical_events=0,
        sha256=batch.sha256,
        mapping_version=batch.mapping_version,
    )


@router.get("/evaluation/latest")
def latest_evaluation(db: Session = Depends(get_db)) -> dict[str, object]:
    run = db.scalar(
        select(DetectionRun)
        .where(DetectionRun.domain_pack == "AI_MISUSE")
        .order_by(DetectionRun.id.desc())
        .limit(1)
    )
    if not run:
        raise HTTPException(status_code=404, detail="No AI misuse evaluation run has been completed.")
    events = db.scalars(
        select(NormalizedEvent).where(
            NormalizedEvent.ingest_batch_id == run.ingest_batch_id,
            NormalizedEvent.hazard_domain == "AI_MISUSE",
        )
    ).all()
    rows = db.execute(
        select(Alert, NormalizedEvent, DetectionRule)
        .join(AlertEvidence, AlertEvidence.alert_id == Alert.id)
        .join(NormalizedEvent, NormalizedEvent.id == AlertEvidence.event_id)
        .join(Indicator, Indicator.id == AlertEvidence.indicator_id)
        .join(DetectionRule, DetectionRule.id == Indicator.detection_rule_id)
        .where(Alert.detection_run_id == run.id)
    ).all()
    levels: dict[str, list[str]] = defaultdict(list)
    trigger_counts: Counter[str] = Counter()
    for alert, event, rule in rows:
        levels[event.source_record_id].append(alert.recommended_review_level or "MR0")
        trigger_counts[rule.rule_id] += 1
    rank = {"MR0": 0, "MR1": 1, "MR2": 2, "MR3": 3}
    exact = 0
    missed = 0
    unexpected = 0
    expected_alerts = 0
    for event in events:
        expected = str((event.severity_features or {}).get("expected_review_level", "MR0"))
        generated = max(levels.get(event.source_record_id, ["MR0"]), key=lambda level: rank[level])
        expected_alerts += int(expected != "MR0")
        exact += int(expected == generated)
        missed += int(rank[expected] >= rank["MR2"] and rank[generated] < rank[expected])
        unexpected += int(rank[expected] <= rank["MR1"] and rank[generated] >= rank["MR2"])
    return {
        "evaluation_set": FIXTURE_VERSION,
        "detection_run_id": run.id,
        "cases_evaluated": len(events),
        "expected_alert_cases": expected_alerts,
        "alerts_generated": run.alert_count,
        "exact_routing_agreement": exact,
        "missed_escalation_cases": missed,
        "unexpected_escalations": unexpected,
        "rule_trigger_counts": dict(trigger_counts),
        "claim_limit": "Fixture conformance only; not real-world model safety performance.",
    }
