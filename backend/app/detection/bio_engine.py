from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.domain_packs.cbrne.bio_monitoring_rules import (
    DEFAULT_RULES,
    RULE_SET_VERSION,
    cdc_above_prior_max,
)
from app.models import Alert, AlertEvidence, DetectionRule, DetectionRun, Indicator, NormalizedEvent


def ensure_bio_rules(db: Session) -> dict[str, DetectionRule]:
    rules = {
        rule.rule_id: rule
        for rule in db.scalars(
            select(DetectionRule).where(
                DetectionRule.domain_pack == "CBRNE_BIO",
                DetectionRule.version == RULE_SET_VERSION,
            )
        ).all()
    }
    for rule_data in DEFAULT_RULES:
        if rule_data["rule_id"] not in rules:
            rule = DetectionRule(
                domain_pack="CBRNE_BIO",
                version=RULE_SET_VERSION,
                active=True,
                **rule_data,
            )
            db.add(rule)
            db.flush()
            rules[rule.rule_id] = rule
    return rules


def create_bio_alert(
    db: Session,
    run: DetectionRun,
    rule: DetectionRule,
    event: NormalizedEvent,
    *,
    score: int,
    priority: str,
    label: str,
    rationale: str,
    evidence: dict[str, object],
) -> None:
    indicator = Indicator(
        event_id=event.id,
        detection_run_id=run.id,
        detection_rule_id=rule.id,
        evidence=evidence,
        indicator_score=score,
    )
    db.add(indicator)
    db.flush()
    alert = Alert(
        detection_run_id=run.id,
        title=f"{rule.title}: {event.source_record_id}",
        priority=priority,
        result_label=label,
        score=score,
        confidence="SOURCE_DERIVED",
        recommended_threat_level="TL1",
        review_framework="THREAT_LEVEL",
        recommended_review_level="TL1",
        rationale=rationale,
    )
    db.add(alert)
    db.flush()
    db.add(AlertEvidence(alert_id=alert.id, event_id=event.id, indicator_id=indicator.id))
    record_audit(db, "ALERT_CREATED", "alert", alert.id, metadata={"rule_id": rule.rule_id})


def run_bio_detection(db: Session, ingest_batch_id: int | None) -> DetectionRun:
    rules = ensure_bio_rules(db)
    query = select(NormalizedEvent).where(NormalizedEvent.hazard_domain == "BIO")
    if ingest_batch_id is not None:
        query = query.where(NormalizedEvent.ingest_batch_id == ingest_batch_id)
    events = list(db.scalars(query).all())
    run = DetectionRun(
        ingest_batch_id=ingest_batch_id,
        domain_pack="CBRNE_BIO",
        rule_set_version=RULE_SET_VERSION,
        event_count=len(events),
    )
    db.add(run)
    db.flush()
    alert_count = 0
    for event in events:
        features = event.severity_features or {}
        if features.get("source_system") == "CDC_NNDSS":
            result = cdc_above_prior_max(features)
            if result:
                score, priority, _ = result
                create_bio_alert(
                    db,
                    run,
                    rules["BIO-SURVEILLANCE-ABOVE-PRIOR-MAX-001"],
                    event,
                    score=score,
                    priority=priority,
                    label="INDICATOR",
                    rationale=(
                        "The CDC NNDSS provisional current-week count is above the source-published "
                        "prior 52-week maximum. This requires analyst review and does not identify "
                        "cause, intent, or a CBRN-E incident."
                    ),
                    evidence=features,
                )
                alert_count += 1
        elif features.get("source_system") == "WHO_DON":
            create_bio_alert(
                db,
                run,
                rules["BIO-OFFICIAL-OUTBREAK-REPORT-001"],
                event,
                score=20,
                priority="LOW",
                label="OBSERVATION",
                rationale=(
                    "WHO has published a Disease Outbreak News record for analyst context. "
                    "An official public report is not a finding of deliberate release or threat intent."
                ),
                evidence=features,
            )
            alert_count += 1
    run.alert_count = alert_count
    record_audit(
        db,
        "DETECTION_RUN_COMPLETED",
        "detection_run",
        run.id,
        metadata={"domain_pack": "CBRNE_BIO", "rule_set_version": RULE_SET_VERSION},
    )
    db.commit()
    db.refresh(run)
    return run
