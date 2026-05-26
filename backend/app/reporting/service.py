from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.models import (
    Alert,
    AlertEvidence,
    AnalystReview,
    DetectionRule,
    DetectionRun,
    Indicator,
    NormalizedEvent,
    Report,
    Source,
)


CLAIM_SUMMARIES = {
    "CBRNE_CHEM": (
        "This report summarizes official source-derived chemical/hazmat analyst review indicators. "
        "Detections are based on public reporting records and do not establish deliberate release, "
        "malicious intent, or mandatory external notification requirements."
    ),
    "CBRNE_BIO": (
        "This report summarizes official public-health surveillance and outbreak reporting analyst "
        "review indicators. CDC NNDSS counts are provisional and subject to revision. WHO Disease "
        "Outbreak News reports are official public-health event notices. Neither source establishes "
        "deliberate release, intent, or CBRN-E attribution."
    ),
    "AI_MISUSE": (
        "This report summarizes AI misuse risk assessment fixture conformance review records. "
        "Results reflect controlled fixture routing behavior only. This is not real-world model "
        "safety performance or operational threat detection."
    ),
    "FRAUD_MONITORING": (
        "This report summarizes fraud risk assessment fixture conformance review records. "
        "Results reflect controlled synthetic fixture routing behavior only. This is not "
        "real-world fraud detection performance, real transaction data, or an operational "
        "threat determination."
    ),
}


def iso_value(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def evidence_for_alert(db: Session, alert_id: int) -> tuple[list[dict[str, object]], list[str], list[str]]:
    rows = db.execute(
        select(AlertEvidence, NormalizedEvent, Indicator, DetectionRule, Source)
        .join(NormalizedEvent, AlertEvidence.event_id == NormalizedEvent.id)
        .join(Indicator, AlertEvidence.indicator_id == Indicator.id)
        .join(DetectionRule, Indicator.detection_rule_id == DetectionRule.id)
        .join(Source, NormalizedEvent.source_id == Source.id)
        .where(AlertEvidence.alert_id == alert_id)
    ).all()
    evidence: list[dict[str, object]] = []
    rule_ids: list[str] = []
    limits: list[str] = []
    for _, event, indicator, rule, source in rows:
        if rule.rule_id not in rule_ids:
            rule_ids.append(rule.rule_id)
        if event.limitations not in limits:
            limits.append(event.limitations)
        evidence.append(
            {
                "event_id": event.id,
                "source_name": source.name,
                "source_record_id": event.source_record_id,
                "source_citation": event.source_url or source.url,
                "hazard_domain": event.hazard_domain,
                "event_type": event.event_type,
                "region": event.region,
                "source_limitations": event.limitations,
                "indicator_score": indicator.indicator_score,
                "indicator_evidence": indicator.evidence,
            }
        )
    return evidence, rule_ids, limits


def create_report_payload(db: Session, title: str, alert_ids: list[int]) -> dict[str, object]:
    selected_ids = list(dict.fromkeys(alert_ids))
    alerts = list(db.scalars(select(Alert).where(Alert.id.in_(selected_ids))).all())
    if len(alerts) != len(selected_ids):
        raise HTTPException(status_code=404, detail="One or more selected alerts were not found.")
    alert_by_id = {alert.id: alert for alert in alerts}
    ordered_alerts = [alert_by_id[alert_id] for alert_id in selected_ids]
    runs = {alert.id: db.get(DetectionRun, alert.detection_run_id) for alert in ordered_alerts}
    domains = {run.domain_pack for run in runs.values() if run is not None}
    versions = {run.rule_set_version for run in runs.values() if run is not None}
    if len(domains) != 1:
        raise HTTPException(status_code=409, detail="A report cannot mix alerts from different domain packs.")
    if len(versions) != 1:
        raise HTTPException(status_code=409, detail="A report cannot mix alerts from different rule-set versions.")
    domain_pack = domains.pop()
    rule_set_version = versions.pop()
    claim_summary = CLAIM_SUMMARIES.get(domain_pack)
    if not claim_summary:
        raise HTTPException(status_code=409, detail="The selected domain pack is not report-enabled.")

    report_alerts: list[dict[str, object]] = []
    for alert in ordered_alerts:
        review = db.scalar(
            select(AnalystReview)
            .where(AnalystReview.alert_id == alert.id)
            .order_by(AnalystReview.id.desc())
            .limit(1)
        )
        if not review:
            raise HTTPException(
                status_code=409,
                detail=f"Alert {alert.id} has not been analyst-reviewed and cannot be reported.",
            )
        evidence, rule_ids, limits = evidence_for_alert(db, alert.id)
        report_alerts.append(
            {
                "alert_id": alert.id,
                "alert_title": alert.title,
                "rule_ids": rule_ids,
                "review_framework": alert.review_framework,
                "review_level": review.review_level or review.threat_level,
                "rule_rationale": alert.rationale,
                "claim_limits": limits,
                "analyst_disposition": review.disposition,
                "analyst_notes": review.note,
                "reviewer": review.reviewer,
                "reviewed_at": iso_value(review.reviewed_at),
                "evidence": evidence,
            }
        )

    report = Report(
        domain_pack=domain_pack,
        rule_set_version=rule_set_version,
        title=title.strip(),
        alert_ids=selected_ids,
        claim_summary=claim_summary,
        report_data={},
    )
    db.add(report)
    db.flush()
    db.refresh(report)
    payload = {
        "report_id": report.id,
        "generated_at": iso_value(report.generated_at),
        "domain_pack": domain_pack,
        "rule_set_version": rule_set_version,
        "title": report.title,
        "claim_summary": claim_summary,
        "alerts": report_alerts,
    }
    report.report_data = payload
    record_audit(
        db,
        "REPORT_GENERATED",
        "report",
        report.id,
        metadata={"domain_pack": domain_pack, "rule_set_version": rule_set_version, "alert_ids": selected_ids},
    )
    db.commit()
    return payload
