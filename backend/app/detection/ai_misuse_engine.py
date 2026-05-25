from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.domain_packs.ai_misuse.rules import (
    DEFAULT_RULES,
    RULE_SET_VERSION,
    matched_rule_ids,
    result_for_rule,
)
from app.models import Alert, AlertEvidence, DetectionRule, DetectionRun, Indicator, NormalizedEvent


def ensure_rules(db: Session) -> dict[str, DetectionRule]:
    rules = {
        rule.rule_id: rule
        for rule in db.scalars(
            select(DetectionRule).where(
                DetectionRule.domain_pack == "AI_MISUSE",
                DetectionRule.version == RULE_SET_VERSION,
            )
        ).all()
    }
    for rule_data in DEFAULT_RULES:
        if rule_data["rule_id"] not in rules:
            rule = DetectionRule(
                domain_pack="AI_MISUSE", version=RULE_SET_VERSION, active=True, **rule_data
            )
            db.add(rule)
            db.flush()
            rules[rule.rule_id] = rule
    return rules


def run_ai_misuse_detection(db: Session, ingest_batch_id: int | None) -> DetectionRun:
    rules = ensure_rules(db)
    query = select(NormalizedEvent).where(NormalizedEvent.hazard_domain == "AI_MISUSE")
    if ingest_batch_id is not None:
        query = query.where(NormalizedEvent.ingest_batch_id == ingest_batch_id)
    events = db.scalars(query).all()
    run = DetectionRun(
        ingest_batch_id=ingest_batch_id,
        domain_pack="AI_MISUSE",
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
                    "trigger_fields": {
                        key: features.get(key)
                        for key in (
                            "intent_context",
                            "assistance_type",
                            "safeguard_evasion",
                            "concealment_or_detection_avoidance",
                            "tool_or_agent_enablement",
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
                result_label="SAFETY_REVIEW",
                score=score,
                confidence="FIXTURE_DERIVED",
                recommended_threat_level="N/A",
                review_framework="AI_MISUSE_REVIEW",
                recommended_review_level=review_level,
                rationale=(
                    f"{rule.rationale} This is a safe synthetic evaluation case, "
                    "not a real user record or incident."
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
                actor="ai_misuse_engine",
                metadata={"rule_id": rule.rule_id, "review_framework": "AI_MISUSE_REVIEW"},
            )
            alert_count += 1
    run.alert_count = alert_count
    record_audit(
        db,
        "DETECTION_RUN_COMPLETED",
        "detection_run",
        run.id,
        actor="ai_misuse_engine",
        metadata={"alerts": alert_count, "evaluation_set": "AI_MISUSE_SAFE_EVAL_V0.1"},
    )
    db.commit()
    db.refresh(run)
    return run
