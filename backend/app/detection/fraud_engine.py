from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.domain_packs.fraud.rules import DEFAULT_RULES, RULE_SET_VERSION, matched_rule_ids, result_for_rule
from app.models import Alert, AlertEvidence, DetectionRule, DetectionRun, Indicator, NormalizedEvent


def ensure_rules(db: Session) -> dict[str, DetectionRule]:
    rules = {
        rule.rule_id: rule
        for rule in db.scalars(
            select(DetectionRule).where(
                DetectionRule.domain_pack == "FRAUD_MONITORING",
                DetectionRule.version == RULE_SET_VERSION,
            )
        ).all()
    }
    for rule_data in DEFAULT_RULES:
        if rule_data["rule_id"] not in rules:
            rule = DetectionRule(
                domain_pack="FRAUD_MONITORING", version=RULE_SET_VERSION, active=True, **rule_data
            )
            db.add(rule)
            db.flush()
            rules[rule.rule_id] = rule
    return rules


def run_fraud_detection(db: Session, ingest_batch_id: int | None) -> DetectionRun:
    rules = ensure_rules(db)
    query = select(NormalizedEvent).where(NormalizedEvent.hazard_domain == "FRAUD")
    if ingest_batch_id is not None:
        query = query.where(NormalizedEvent.ingest_batch_id == ingest_batch_id)
    events = db.scalars(query).all()
    run = DetectionRun(
        ingest_batch_id=ingest_batch_id,
        domain_pack="FRAUD_MONITORING",
        rule_set_version=RULE_SET_VERSION,
        event_count=len(events),
    )
    db.add(run)
    db.flush()
    alert_count = 0
    for event in events:
        features = event.severity_features or {}
        for rule_id in matched_rule_ids(features):
            score, priority, review_level = result_for_rule(rule_id)
            rule = rules[rule_id]
            indicator = Indicator(
                event_id=event.id,
                detection_run_id=run.id,
                detection_rule_id=rule.id,
                evidence={
                    "case_id": event.source_record_id,
                    "case_version": features.get("case_version"),
                    "trigger_categories": {
                        key: features.get(key)
                        for key in (
                            "velocity_indicator",
                            "duplicate_indicator",
                            "amount_outlier_indicator",
                            "identity_consistency_indicator",
                        )
                    },
                    "safe_abstract_summary": event.narrative,
                    "limitation": event.limitations,
                },
                indicator_score=score,
            )
            db.add(indicator)
            db.flush()
            alert = Alert(
                detection_run_id=run.id,
                title=f"{rule.title}: {event.source_record_id}",
                priority=priority,
                result_label="FRAUD_REVIEW",
                score=score,
                confidence="FIXTURE_DERIVED",
                recommended_threat_level="N/A",
                review_framework="FRAUD_REVIEW",
                recommended_review_level=review_level,
                rationale=(
                    f"{rule.rationale} This is a controlled synthetic evaluation case, "
                    "not a real transaction or confirmed fraud outcome."
                ),
            )
            db.add(alert)
            db.flush()
            db.add(AlertEvidence(alert_id=alert.id, event_id=event.id, indicator_id=indicator.id))
            record_audit(
                db,
                "ALERT_CREATED",
                "alert",
                alert.id,
                actor="fraud_engine",
                metadata={"rule_id": rule.rule_id, "review_framework": "FRAUD_REVIEW"},
            )
            alert_count += 1
    run.alert_count = alert_count
    record_audit(
        db,
        "DETECTION_RUN_COMPLETED",
        "detection_run",
        run.id,
        actor="fraud_engine",
        metadata={"alerts": alert_count, "evaluation_set": "FRAUD_SAFE_EVAL_V0.1"},
    )
    db.commit()
    db.refresh(run)
    return run
