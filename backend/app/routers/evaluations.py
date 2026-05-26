from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.database import get_db
from app.evaluation.service import (
    comparison_detail,
    evaluation_run_detail,
    execute_evaluation,
    register_ai_misuse_fixture,
    register_fraud_fixture,
    validate_case_level,
)
from app.models import DetectionRun, EvaluationCase, EvaluationRun, EvaluationSet, NormalizedEvent
from app.schemas.api import EvaluationCaseCreate, EvaluationRunCreate, EvaluationSetCreate


router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/sets")
def list_evaluation_sets(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    sets = list(db.scalars(select(EvaluationSet).order_by(EvaluationSet.id.desc())).all())
    results = []
    for evaluation_set in sets:
        latest = db.scalar(
            select(EvaluationRun)
            .where(EvaluationRun.evaluation_set_id == evaluation_set.id)
            .order_by(EvaluationRun.id.desc())
            .limit(1)
        )
        results.append(
            {
                "id": evaluation_set.id,
                "name": evaluation_set.name,
                "version": evaluation_set.version,
                "domain_pack": evaluation_set.domain_pack,
                "review_framework": evaluation_set.review_framework,
                "evaluation_type": evaluation_set.evaluation_type,
                "status": evaluation_set.status,
                "claim_limit": evaluation_set.claim_limit,
                "latest_evaluation_run_id": latest.id if latest else None,
                "latest_rule_set_version": latest.rule_set_version if latest else None,
                "latest_case_count": latest.case_count if latest else None,
            }
        )
    return results


@router.get("/detection-runs")
def list_detection_runs(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    runs = db.scalars(select(DetectionRun).order_by(DetectionRun.id.desc()).limit(25)).all()
    return [
        {
            "id": run.id,
            "domain_pack": run.domain_pack,
            "rule_set_version": run.rule_set_version,
            "event_count": run.event_count,
            "alert_count": run.alert_count,
            "executed_at": run.executed_at,
        }
        for run in runs
    ]


@router.get("/sets/{evaluation_set_id}/runs")
def list_set_runs(evaluation_set_id: int, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    if not db.get(EvaluationSet, evaluation_set_id):
        raise HTTPException(status_code=404, detail="Evaluation set not found.")
    runs = db.scalars(
        select(EvaluationRun)
        .where(EvaluationRun.evaluation_set_id == evaluation_set_id)
        .order_by(EvaluationRun.id.desc())
    ).all()
    return [
        {
            "id": run.id,
            "detection_run_id": run.detection_run_id,
            "rule_set_version": run.rule_set_version,
            "case_count": run.case_count,
        }
        for run in runs
    ]


@router.post("/register-ai-misuse-fixture", status_code=201)
def register_fixture(db: Session = Depends(get_db)) -> dict[str, int | str]:
    evaluation_set = register_ai_misuse_fixture(db)
    return {"evaluation_set_id": evaluation_set.id, "status": evaluation_set.status}


@router.post("/register-fraud-fixture", status_code=201)
def register_fraud_evaluation(db: Session = Depends(get_db)) -> dict[str, int | str]:
    evaluation_set = register_fraud_fixture(db)
    return {"evaluation_set_id": evaluation_set.id, "status": evaluation_set.status}


@router.post("/sets", status_code=201)
def create_evaluation_set(payload: EvaluationSetCreate, db: Session = Depends(get_db)) -> dict[str, int | str]:
    expected_framework = {
        "AI_MISUSE": "AI_MISUSE_REVIEW",
        "FRAUD_MONITORING": "FRAUD_REVIEW",
    }.get(payload.domain_pack, "THREAT_LEVEL")
    if payload.review_framework != expected_framework:
        raise HTTPException(status_code=422, detail="Review framework must match the domain pack.")
    if payload.domain_pack == "CBRNE_CHEM" and payload.evaluation_type != "REVIEWED_BENCHMARK":
        raise HTTPException(status_code=422, detail="CHEM Stage 5 sets must be reviewed benchmarks.")
    evaluation_set = EvaluationSet(**payload.model_dump())
    db.add(evaluation_set)
    db.flush()
    record_audit(
        db,
        "EVALUATION_SET_CREATED",
        "evaluation_set",
        evaluation_set.id,
        metadata={"domain_pack": payload.domain_pack, "evaluation_type": payload.evaluation_type},
    )
    db.commit()
    return {"evaluation_set_id": evaluation_set.id, "status": evaluation_set.status}


@router.post("/sets/{evaluation_set_id}/cases", status_code=201)
def add_evaluation_case(
    evaluation_set_id: int, payload: EvaluationCaseCreate, db: Session = Depends(get_db)
) -> dict[str, int | str]:
    evaluation_set = db.get(EvaluationSet, evaluation_set_id)
    if not evaluation_set:
        raise HTTPException(status_code=404, detail="Evaluation set not found.")
    event = db.get(NormalizedEvent, payload.normalized_event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Normalized event not found.")
    event_pack = {
        "AI_MISUSE": "AI_MISUSE",
        "CHEM": "CBRNE_CHEM",
        "FRAUD": "FRAUD_MONITORING",
    }.get(event.hazard_domain)
    if not event_pack:
        raise HTTPException(status_code=409, detail="This event domain is not supported by Stage 5 evaluation.")
    if evaluation_set.domain_pack != event_pack:
        raise HTTPException(status_code=409, detail="Evaluation set and event domain packs do not match.")
    if evaluation_set.evaluation_type == "REVIEWED_BENCHMARK" and (
        not payload.citation.strip() or not payload.label_rationale.strip()
    ):
        raise HTTPException(status_code=422, detail="Reviewed benchmark cases require citation and rationale.")
    validate_case_level(evaluation_set, payload.expected_review_level)
    case = EvaluationCase(
        evaluation_set_id=evaluation_set.id,
        source_record_id=event.source_record_id,
        **payload.model_dump(),
    )
    db.add(case)
    db.flush()
    record_audit(
        db,
        "EVALUATION_CASE_ADDED",
        "evaluation_case",
        case.id,
        metadata={"evaluation_set_id": evaluation_set.id, "source_record_id": event.source_record_id},
    )
    db.commit()
    return {"evaluation_case_id": case.id, "status": case.label_status}


@router.post("/run", status_code=201)
def run_evaluation(payload: EvaluationRunCreate, db: Session = Depends(get_db)) -> dict[str, int | str]:
    evaluation_set = db.get(EvaluationSet, payload.evaluation_set_id)
    detection_run = db.get(DetectionRun, payload.detection_run_id)
    if not evaluation_set or not detection_run:
        raise HTTPException(status_code=404, detail="Evaluation set or detection run not found.")
    evaluation_run = execute_evaluation(db, evaluation_set, detection_run)
    return {"evaluation_run_id": evaluation_run.id, "status": "COMPLETED"}


@router.get("/runs/{evaluation_run_id}")
def get_evaluation_run(evaluation_run_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    evaluation_run = db.get(EvaluationRun, evaluation_run_id)
    if not evaluation_run:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")
    return evaluation_run_detail(db, evaluation_run)


@router.get("/compare")
def compare_evaluation_runs(
    baseline_evaluation_run_id: int,
    candidate_evaluation_run_id: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    baseline = db.get(EvaluationRun, baseline_evaluation_run_id)
    candidate = db.get(EvaluationRun, candidate_evaluation_run_id)
    if not baseline or not candidate:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")
    return comparison_detail(db, baseline, candidate)
