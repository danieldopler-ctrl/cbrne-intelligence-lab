from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.domain_packs.cbrne.chem_hazmat_rules import (
    DEFAULT_RULES,
    RULE_SET_VERSION,
    consequence_result,
    potential_release_result,
    substance_result,
)
from app.domain_packs.cbrne.epa_rmp_toxic_substances import EPA_RMP_TOXIC_REFERENCE_URL
from app.models import Alert, AlertEvidence, DetectionRule, DetectionRun, Indicator, NormalizedEvent


def ensure_rules(db: Session) -> dict[str, DetectionRule]:
    rules = {
        rule.rule_id: rule
        for rule in db.scalars(
            select(DetectionRule).where(DetectionRule.version == RULE_SET_VERSION)
        ).all()
    }
    for rule_data in DEFAULT_RULES:
        if rule_data["rule_id"] not in rules:
            rule = DetectionRule(
                domain_pack="CBRNE_CHEM", version=RULE_SET_VERSION, active=True, **rule_data
            )
            db.add(rule)
            db.flush()
            rules[rule.rule_id] = rule
    return rules


def create_alert(
    db: Session,
    run: DetectionRun,
    rule: DetectionRule,
    event: NormalizedEvent,
    *,
    score: int,
    priority: str,
    recommended_level: str,
    label: str,
    rationale: str,
    evidence: dict,
) -> Alert:
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
        recommended_threat_level=recommended_level,
        rationale=rationale,
    )
    db.add(alert)
    db.flush()
    db.add(AlertEvidence(alert_id=alert.id, event_id=event.id, indicator_id=indicator.id))
    record_audit(db, "ALERT_CREATED", "alert", alert.id, metadata={"rule_id": rule.rule_id})
    return alert


def run_detection(
    db: Session, ingest_batch_id: int | None, *, include_observations: bool = False
) -> DetectionRun:
    rules = ensure_rules(db)
    query = select(NormalizedEvent)
    if ingest_batch_id is not None:
        query = query.where(NormalizedEvent.ingest_batch_id == ingest_batch_id)
    events = db.scalars(query).all()
    run = DetectionRun(
        ingest_batch_id=ingest_batch_id,
        domain_pack="CBRNE_CHEM",
        rule_set_version=RULE_SET_VERSION,
        event_count=len(events),
    )
    db.add(run)
    db.flush()
    alert_count = 0
    period_regions = Counter(
        (event.region, event.event_date[:7])
        for event in events
        if event.hazard_domain == "CHEM" and event.region and event.event_date and len(event.event_date) >= 7
    )
    cluster_alerted: set[tuple[str, str]] = set()
    for event in events:
        result = consequence_result(event.severity_features or {})
        if result:
            score, priority, level = result
            create_alert(
                db,
                run,
                rules["CHEM-CONSEQUENCE-001"],
                event,
                score=score,
                priority=priority,
                recommended_level=level,
                label="INDICATOR",
                rationale="Source-reported consequence fields exceed the documented review threshold.",
                evidence=event.severity_features,
            )
            alert_count += 1
        quantity_result = potential_release_result(event.severity_features or {})
        if event.hazard_domain == "CHEM" and quantity_result:
            score, priority, level = quantity_result
            create_alert(
                db,
                run,
                rules["CHEM-POTENTIAL-RELEASE-001"],
                event,
                score=score,
                priority=priority,
                recommended_level=level,
                label="INDICATOR",
                rationale=(
                    "Source reports a large maximum potential release. Quantity is not confirmed "
                    "actual release and does not account for chemical-specific hazard."
                ),
                evidence={"maximum_potential_release_gallons": event.severity_features["quantity_released"]},
            )
            alert_count += 1
        substance_match = substance_result(event.commodity)
        if event.hazard_domain == "CHEM" and substance_match:
            score, priority, level, match = substance_match
            create_alert(
                db,
                run,
                rules["CHEM-SUBSTANCE-001"],
                event,
                score=score,
                priority=priority,
                recommended_level=level,
                label="INDICATOR",
                rationale=(
                    "Source commodity text matches an EPA RMP regulated toxic substance. "
                    "This is a review priority signal, not a finding of intent, quantity, "
                    "release consequence, or regulatory applicability."
                ),
                evidence={
                    "source_commodity": match.source_commodity,
                    "epa_rmp_toxic_substance": match.regulated_substance,
                    "match_method": match.match_method,
                    "reference": EPA_RMP_TOXIC_REFERENCE_URL,
                },
            )
            alert_count += 1
        if include_observations and event.hazard_domain == "CHEM" and "release" in event.event_type.lower():
            create_alert(
                db,
                run,
                rules["CHEM-RELEASE-001"],
                event,
                score=20,
                priority="LOW",
                recommended_level="TL1",
                label="OBSERVATION",
                rationale="Source record identifies a chemical or hazardous-material release.",
                evidence={"event_type": event.event_type, "hazard_domain": event.hazard_domain},
            )
            alert_count += 1
        cluster_key = (
            (event.region, event.event_date[:7])
            if event.region and event.event_date and len(event.event_date) >= 7
            else None
        )
        if (
            event.hazard_domain == "CHEM"
            and cluster_key
            and period_regions[cluster_key] >= 3
            and cluster_key not in cluster_alerted
        ):
            create_alert(
                db,
                run,
                rules["CHEM-RECURRENCE-001"],
                event,
                score=55,
                priority="MEDIUM",
                recommended_level="TL2",
                label="INDICATOR",
                rationale=(
                    "Three or more chemical records share the mapped reporting region and month. "
                    "Baseline calibration is required before labeling this pattern anomalous."
                ),
                evidence={
                    "region": cluster_key[0],
                    "calendar_month": cluster_key[1],
                    "cluster_count": period_regions[cluster_key],
                },
            )
            alert_count += 1
            cluster_alerted.add(cluster_key)
    run.alert_count = alert_count
    record_audit(db, "DETECTION_RUN_COMPLETED", "detection_run", run.id, metadata={"alerts": alert_count})
    db.commit()
    db.refresh(run)
    return run
