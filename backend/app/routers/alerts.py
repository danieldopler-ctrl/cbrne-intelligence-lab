from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.database import get_db
from app.models import (
    Alert,
    AlertEvidence,
    AnalystReview,
    DetectionRun,
    Indicator,
    NormalizedEvent,
    NotificationAction,
    PlanApplicabilityReview,
)
from app.schemas.api import (
    AlertDetail,
    AlertOut,
    NotificationCreate,
    PlanReviewCreate,
    ReviewCreate,
)


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status: str | None = None,
    detection_run_id: int | None = None,
    domain_pack: str | None = None,
    include_history: bool = False,
    db: Session = Depends(get_db),
) -> list[Alert]:
    query = select(Alert).order_by(Alert.score.desc(), Alert.created_at.desc())
    if detection_run_id is not None:
        query = query.where(Alert.detection_run_id == detection_run_id)
    elif not include_history:
        latest_query = select(DetectionRun.id).order_by(DetectionRun.id.desc()).limit(1)
        if domain_pack:
            latest_query = latest_query.where(DetectionRun.domain_pack == domain_pack)
        latest_run_id = db.scalar(latest_query)
        if latest_run_id is not None:
            query = query.where(Alert.detection_run_id == latest_run_id)
        elif domain_pack:
            return []
    elif domain_pack:
        query = query.join(DetectionRun).where(DetectionRun.domain_pack == domain_pack)
    if status:
        query = query.where(Alert.status == status)
    return list(db.scalars(query).all())


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> AlertDetail:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    evidence_rows = db.execute(
        select(AlertEvidence, NormalizedEvent, Indicator)
        .join(NormalizedEvent, AlertEvidence.event_id == NormalizedEvent.id)
        .join(Indicator, AlertEvidence.indicator_id == Indicator.id)
        .where(AlertEvidence.alert_id == alert_id)
    ).all()
    reviews = db.scalars(select(AnalystReview).where(AnalystReview.alert_id == alert_id)).all()
    notifications = db.scalars(
        select(NotificationAction).where(NotificationAction.alert_id == alert_id)
    ).all()
    plans = db.scalars(
        select(PlanApplicabilityReview).where(PlanApplicabilityReview.alert_id == alert_id)
    ).all()
    return AlertDetail(
        **AlertOut.model_validate(alert).model_dump(),
        evidence=[
            {
                "event_id": event.id,
                "source_record_id": event.source_record_id,
                "event_type": event.event_type,
                "region": event.region,
                "source_url": event.source_url,
                "limitations": event.limitations,
                "indicator_score": indicator.indicator_score,
                "evidence": indicator.evidence,
            }
            for _, event, indicator in evidence_rows
        ],
        reviews=[
            {
                "reviewer": review.reviewer,
                "disposition": review.disposition,
                "threat_level": review.threat_level,
                "review_framework": review.review_framework,
                "review_level": review.review_level,
                "note": review.note,
                "reviewed_at": review.reviewed_at,
            }
            for review in reviews
        ],
        notifications=[
            {
                "route_type": item.route_type,
                "route_name": item.route_name,
                "reporting_assessment": item.reporting_assessment,
                "reference_number": item.reference_number,
                "rationale": item.rationale,
            }
            for item in notifications
        ],
        plan_reviews=[
            {
                "plan_code": item.plan_code,
                "applicability": item.applicability,
                "activation_status": item.activation_status,
                "rationale": item.rationale,
                "incident_reference": item.incident_reference,
            }
            for item in plans
        ],
    )


@router.post("/{alert_id}/reviews", response_model=AlertOut)
def review_alert(alert_id: int, payload: ReviewCreate, db: Session = Depends(get_db)) -> Alert:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    if alert.review_framework == "AI_MISUSE_REVIEW":
        if not payload.review_level:
            raise HTTPException(status_code=422, detail="Misuse review requires an MR0-MR3 review level.")
        review = AnalystReview(
            alert_id=alert_id,
            reviewer=payload.reviewer,
            disposition=payload.disposition,
            threat_level="N/A",
            review_framework="AI_MISUSE_REVIEW",
            review_level=payload.review_level,
            note=payload.note,
        )
        alert.confirmed_review_level = payload.review_level
        level_metadata = {"review_framework": "AI_MISUSE_REVIEW", "review_level": payload.review_level}
    else:
        if not payload.threat_level:
            raise HTTPException(status_code=422, detail="Threat review requires a TL0-TL4 threat level.")
        review = AnalystReview(
            alert_id=alert_id,
            reviewer=payload.reviewer,
            disposition=payload.disposition,
            threat_level=payload.threat_level,
            review_framework="THREAT_LEVEL",
            review_level=payload.threat_level,
            note=payload.note,
        )
        alert.confirmed_threat_level = payload.threat_level
        alert.confirmed_review_level = payload.threat_level
        level_metadata = {"review_framework": "THREAT_LEVEL", "threat_level": payload.threat_level}
    db.add(review)
    alert.status = payload.disposition
    record_audit(
        db,
        "ALERT_REVIEWED",
        "alert",
        alert_id,
        actor=payload.reviewer,
        metadata={"disposition": payload.disposition, **level_metadata},
    )
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/{alert_id}/notifications", status_code=201)
def add_notification(
    alert_id: int, payload: NotificationCreate, db: Session = Depends(get_db)
) -> dict[str, int | str]:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    if alert.review_framework == "AI_MISUSE_REVIEW":
        raise HTTPException(
            status_code=409,
            detail="AI misuse fixture alerts use internal safety review only; notification actions are disabled.",
        )
    action = NotificationAction(alert_id=alert_id, **payload.model_dump())
    db.add(action)
    db.flush()
    record_audit(db, "NOTIFICATION_ASSESSED", "alert", alert_id, metadata=payload.model_dump(mode="json"))
    db.commit()
    return {"id": action.id, "status": "recorded"}


@router.post("/{alert_id}/plan-reviews", status_code=201)
def add_plan_review(
    alert_id: int, payload: PlanReviewCreate, db: Session = Depends(get_db)
) -> dict[str, int | str]:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    if alert.review_framework == "AI_MISUSE_REVIEW":
        raise HTTPException(
            status_code=409,
            detail="AI misuse fixture alerts are not incident records; doctrine review is disabled.",
        )
    review = PlanApplicabilityReview(alert_id=alert_id, **payload.model_dump())
    db.add(review)
    db.flush()
    record_audit(db, "PLAN_APPLICABILITY_REVIEWED", "alert", alert_id, metadata=payload.model_dump())
    db.commit()
    return {"id": review.id, "status": "recorded"}
