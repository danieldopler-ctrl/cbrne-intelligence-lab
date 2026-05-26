from collections import Counter

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
    EvaluationCase,
    EvaluationCaseResult,
    EvaluationRun,
    EvaluationSet,
    Indicator,
    NormalizedEvent,
)


MISUSE_RANK = {"MR0": 0, "MR1": 1, "MR2": 2, "MR3": 3}
THREAT_RANK = {"TL0": 0, "TL1": 1, "TL2": 2, "TL3": 3, "TL4": 4}
FIXTURE_CLAIM_LIMIT = (
    "This report measures agreement with controlled fixture expectations only. "
    "It is not real-world model safety or threat-detection performance."
)
BENCHMARK_CLAIM_LIMIT = (
    "This report measures rule behavior on selected analyst-labeled public-source benchmark records. "
    "It does not establish intent, population-level detection rates, or operational readiness."
)


def register_ai_misuse_fixture(db: Session) -> EvaluationSet:
    latest_event = db.scalar(
        select(NormalizedEvent)
        .where(NormalizedEvent.hazard_domain == "AI_MISUSE")
        .order_by(NormalizedEvent.id.desc())
        .limit(1)
    )
    if not latest_event:
        raise HTTPException(
            status_code=409,
            detail="Import the safe AI misuse evaluation set before registering its evaluation record.",
        )
    events = list(
        db.scalars(
            select(NormalizedEvent)
            .where(
                NormalizedEvent.hazard_domain == "AI_MISUSE",
                NormalizedEvent.ingest_batch_id == latest_event.ingest_batch_id,
            )
            .order_by(NormalizedEvent.source_record_id)
        ).all()
    )
    evaluation_set = db.scalar(
        select(EvaluationSet).where(
            EvaluationSet.version == "AI_MISUSE_SAFE_EVAL_V0.1",
            EvaluationSet.domain_pack == "AI_MISUSE",
        )
    )
    if evaluation_set:
        return evaluation_set
    evaluation_set = EvaluationSet(
        name="AI Misuse Safe Evaluation Set V0.1",
        version="AI_MISUSE_SAFE_EVAL_V0.1",
        domain_pack="AI_MISUSE",
        review_framework="AI_MISUSE_REVIEW",
        evaluation_type="FIXTURE_CONFORMANCE",
        description="Public-safe abstract fixture cases for deterministic internal safety-review routing.",
        source_basis="Committed safe abstract fixture; no real prompts, users, incidents, or model calls.",
        claim_limit=FIXTURE_CLAIM_LIMIT,
        status="READY",
    )
    db.add(evaluation_set)
    db.flush()
    for event in events:
        features = event.severity_features or {}
        db.add(
            EvaluationCase(
                evaluation_set_id=evaluation_set.id,
                case_key=event.source_record_id,
                normalized_event_id=event.id,
                source_record_id=event.source_record_id,
                expected_review_level=str(features.get("expected_review_level", "MR0")),
                expected_rule_ids=features.get("expected_rule_ids", []),
                label_rationale="Expected route supplied by the public-safe controlled fixture.",
                citation="AI_MISUSE_SAFE_EVAL_V0.1 committed fixture record.",
                label_status="FIXTURE_LABELED",
            )
        )
    record_audit(
        db,
        "EVALUATION_SET_REGISTERED",
        "evaluation_set",
        evaluation_set.id,
        actor="evaluation_service",
        metadata={"version": evaluation_set.version, "cases": len(events)},
    )
    db.commit()
    db.refresh(evaluation_set)
    return evaluation_set


def validate_case_level(evaluation_set: EvaluationSet, level: str) -> None:
    allowed = MISUSE_RANK if evaluation_set.review_framework == "AI_MISUSE_REVIEW" else THREAT_RANK
    if level not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Expected level must match {evaluation_set.review_framework}: {', '.join(allowed)}.",
        )


def execute_evaluation(db: Session, evaluation_set: EvaluationSet, detection_run: DetectionRun) -> EvaluationRun:
    if evaluation_set.domain_pack != detection_run.domain_pack:
        raise HTTPException(status_code=409, detail="Evaluation set and detection run domain packs do not match.")
    existing = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.evaluation_set_id == evaluation_set.id,
            EvaluationRun.detection_run_id == detection_run.id,
        )
    )
    if existing:
        return existing
    cases = list(
        db.scalars(
            select(EvaluationCase)
            .where(EvaluationCase.evaluation_set_id == evaluation_set.id)
            .order_by(EvaluationCase.id)
        ).all()
    )
    evaluation_run = EvaluationRun(
        evaluation_set_id=evaluation_set.id,
        detection_run_id=detection_run.id,
        rule_set_version=detection_run.rule_set_version,
        evaluation_type=evaluation_set.evaluation_type,
        case_count=len(cases),
    )
    db.add(evaluation_run)
    db.flush()
    for case in cases:
        db.add(_evaluate_case(db, evaluation_set, detection_run, evaluation_run, case))
    record_audit(
        db,
        "EVALUATION_RUN_COMPLETED",
        "evaluation_run",
        evaluation_run.id,
        actor="evaluation_service",
        metadata={"evaluation_set_id": evaluation_set.id, "detection_run_id": detection_run.id},
    )
    db.commit()
    db.refresh(evaluation_run)
    return evaluation_run


def _evaluate_case(
    db: Session,
    evaluation_set: EvaluationSet,
    detection_run: DetectionRun,
    evaluation_run: EvaluationRun,
    case: EvaluationCase,
) -> EvaluationCaseResult:
    zero_level = "MR0" if evaluation_set.review_framework == "AI_MISUSE_REVIEW" else "TL0"
    event = db.get(NormalizedEvent, case.normalized_event_id) if case.normalized_event_id else None
    if (
        event
        and evaluation_set.evaluation_type == "FIXTURE_CONFORMANCE"
        and detection_run.ingest_batch_id is not None
        and event.ingest_batch_id != detection_run.ingest_batch_id
    ):
        event = db.scalar(
            select(NormalizedEvent).where(
                NormalizedEvent.ingest_batch_id == detection_run.ingest_batch_id,
                NormalizedEvent.hazard_domain == event.hazard_domain,
                NormalizedEvent.source_record_id == case.source_record_id,
            )
        )
    in_scope = bool(event) and (
        detection_run.ingest_batch_id is None or event.ingest_batch_id == detection_run.ingest_batch_id
    )
    if not in_scope:
        return EvaluationCaseResult(
            evaluation_run_id=evaluation_run.id,
            evaluation_case_id=case.id,
            generated_review_level=zero_level,
            generated_rule_ids=[],
            alert_ids=[],
            result="NOT_EVALUATED",
            result_rationale="Case event was not within the selected detection run event scope.",
        )
    rows = db.execute(
        select(Alert, DetectionRule)
        .join(AlertEvidence, AlertEvidence.alert_id == Alert.id)
        .join(Indicator, Indicator.id == AlertEvidence.indicator_id)
        .join(DetectionRule, DetectionRule.id == Indicator.detection_rule_id)
        .where(
            Alert.detection_run_id == detection_run.id,
            AlertEvidence.event_id == event.id,
        )
    ).all()
    distinct: dict[int, tuple[Alert, DetectionRule]] = {alert.id: (alert, rule) for alert, rule in rows}
    alerts = list(distinct.values())
    ranks = MISUSE_RANK if evaluation_set.review_framework == "AI_MISUSE_REVIEW" else THREAT_RANK
    levels = [
        (alert.recommended_review_level or alert.recommended_threat_level)
        for alert, _ in alerts
    ]
    generated = max(levels or [zero_level], key=lambda value: ranks[value])
    result, rationale = classify_result(case.expected_review_level, generated, ranks)
    return EvaluationCaseResult(
        evaluation_run_id=evaluation_run.id,
        evaluation_case_id=case.id,
        generated_review_level=generated,
        generated_rule_ids=sorted({rule.rule_id for _, rule in alerts}),
        alert_ids=sorted(distinct),
        result=result,
        result_rationale=rationale,
    )


def classify_result(expected: str, generated: str, ranks: dict[str, int]) -> tuple[str, str]:
    if expected == generated:
        return "MATCH", "Highest generated route matches the documented expected route."
    if ranks[expected] >= 2 and ranks[generated] < ranks[expected]:
        return "MISSED_EXPECTED_PRIORITY", "Generated route falls below a documented expected priority."
    if ranks[expected] <= 1 and ranks[generated] >= 2:
        return "UNEXPECTED_HIGH_PRIORITY", "Generated route exceeds a documented low-priority expectation."
    return "ROUTE_DIFFERENCE", "Generated route differs from the documented expectation."


def evaluation_run_detail(db: Session, evaluation_run: EvaluationRun) -> dict[str, object]:
    evaluation_set = db.get(EvaluationSet, evaluation_run.evaluation_set_id)
    if not evaluation_set:
        raise HTTPException(status_code=404, detail="Evaluation set not found.")
    rows = db.execute(
        select(EvaluationCaseResult, EvaluationCase)
        .join(EvaluationCase, EvaluationCase.id == EvaluationCaseResult.evaluation_case_id)
        .where(EvaluationCaseResult.evaluation_run_id == evaluation_run.id)
        .order_by(EvaluationCaseResult.id)
    ).all()
    result_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    alert_level_counts: Counter[str] = Counter()
    linked_alert_ids: set[int] = set()
    case_results = []
    for result, case in rows:
        result_counts[result.result] += 1
        if result.result != "NOT_EVALUATED":
            level_counts[result.generated_review_level] += 1
        rule_counts.update(result.generated_rule_ids or [])
        linked_alert_ids.update(result.alert_ids or [])
        for alert_id in result.alert_ids or []:
            alert = db.get(Alert, alert_id)
            if alert:
                alert_level_counts[alert.recommended_review_level or alert.recommended_threat_level] += 1
        case_results.append(
            {
                "case_id": case.id,
                "case_key": case.case_key,
                "source_record_id": case.source_record_id,
                "expected_review_level": case.expected_review_level,
                "generated_review_level": result.generated_review_level,
                "generated_rule_ids": result.generated_rule_ids,
                "alert_ids": result.alert_ids,
                "result": result.result,
                "result_rationale": result.result_rationale,
                "citation": case.citation,
                "label_rationale": case.label_rationale,
            }
        )
    disposition_counts = Counter(
        db.scalars(
            select(AnalystReview.disposition).where(AnalystReview.alert_id.in_(linked_alert_ids))
        ).all()
        if linked_alert_ids
        else []
    )
    evaluated = len(rows) - result_counts["NOT_EVALUATED"]
    return {
        "id": evaluation_run.id,
        "evaluation_set": {
            "id": evaluation_set.id,
            "name": evaluation_set.name,
            "version": evaluation_set.version,
            "domain_pack": evaluation_set.domain_pack,
            "review_framework": evaluation_set.review_framework,
            "evaluation_type": evaluation_set.evaluation_type,
            "source_basis": evaluation_set.source_basis,
            "claim_limit": evaluation_set.claim_limit,
        },
        "detection_run_id": evaluation_run.detection_run_id,
        "rule_set_version": evaluation_run.rule_set_version,
        "measures": {
            "cases_in_set": len(rows),
            "cases_evaluated": evaluated,
            "cases_not_evaluated": result_counts["NOT_EVALUATED"],
            "matched_routes": result_counts["MATCH"],
            "missed_expected_priorities": result_counts["MISSED_EXPECTED_PRIORITY"],
            "unexpected_high_priorities": result_counts["UNEXPECTED_HIGH_PRIORITY"],
            "route_differences": result_counts["ROUTE_DIFFERENCE"],
            "alerts_generated_for_cases": sum(len(row.alert_ids or []) for row, _ in rows),
            "alert_workload_by_rule": dict(rule_counts),
            "highest_route_by_level": dict(level_counts),
            "individual_alerts_by_level": dict(alert_level_counts),
            "reviewed_outcomes_available": dict(disposition_counts),
        },
        "case_results": case_results,
        "claim_limit": evaluation_set.claim_limit,
    }


def comparison_detail(db: Session, baseline: EvaluationRun, candidate: EvaluationRun) -> dict[str, object]:
    if baseline.evaluation_set_id != candidate.evaluation_set_id:
        raise HTTPException(status_code=409, detail="Only runs from the same evaluation set can be compared.")
    evaluation_set = db.get(EvaluationSet, baseline.evaluation_set_id)
    if not evaluation_set:
        raise HTTPException(status_code=404, detail="Evaluation set not found.")
    ranks = MISUSE_RANK if evaluation_set.review_framework == "AI_MISUSE_REVIEW" else THREAT_RANK
    base_results = {
        result.evaluation_case_id: result
        for result in db.scalars(
            select(EvaluationCaseResult).where(EvaluationCaseResult.evaluation_run_id == baseline.id)
        ).all()
    }
    candidate_results = {
        result.evaluation_case_id: result
        for result in db.scalars(
            select(EvaluationCaseResult).where(EvaluationCaseResult.evaluation_run_id == candidate.id)
        ).all()
    }
    case_labels = {
        case.id: case.case_key
        for case in db.scalars(
            select(EvaluationCase).where(EvaluationCase.evaluation_set_id == evaluation_set.id)
        ).all()
    }
    route_changes = []
    rule_changes = []
    upgrades = 0
    downgrades = 0
    for case_id, initial in base_results.items():
        updated = candidate_results.get(case_id)
        if not updated:
            continue
        added = sorted(set(updated.generated_rule_ids) - set(initial.generated_rule_ids))
        removed = sorted(set(initial.generated_rule_ids) - set(updated.generated_rule_ids))
        case_change = {
            "case_key": case_labels.get(case_id, str(case_id)),
            "baseline_route": initial.generated_review_level,
            "candidate_route": updated.generated_review_level,
            "rules_added": added,
            "rules_removed": removed,
        }
        if initial.generated_review_level != updated.generated_review_level:
            change = ranks[updated.generated_review_level] - ranks[initial.generated_review_level]
            upgrades += int(change > 0)
            downgrades += int(change < 0)
            route_changes.append(case_change)
        if added or removed:
            rule_changes.append(case_change)
    base_detail = evaluation_run_detail(db, baseline)
    candidate_detail = evaluation_run_detail(db, candidate)
    return {
        "evaluation_set": {"id": evaluation_set.id, "name": evaluation_set.name},
        "baseline": {"evaluation_run_id": baseline.id, "rule_set_version": baseline.rule_set_version},
        "candidate": {"evaluation_run_id": candidate.id, "rule_set_version": candidate.rule_set_version},
        "routes_changed": route_changes,
        "rules_changed_by_case": rule_changes,
        "priority_upgrades": upgrades,
        "priority_downgrades": downgrades,
        "baseline_measures": base_detail["measures"],
        "candidate_measures": candidate_detail["measures"],
        "claim_limit": (
            "This comparison describes selected-case route and workload changes only. "
            + evaluation_set.claim_limit
        ),
    }
