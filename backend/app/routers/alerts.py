from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.database import get_db
from app.models import (
    Alert,
    AlertEvidence,
    AnalystReview,
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
def list_alerts(status: str | None = None, db: Session = Depends(get_db)) -> list[Alert]:
    query = select(Alert).order_by(Alert.score.desc(), Alert.created_at.desc())
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
    db.add(AnalystReview(alert_id=alert_id, **payload.model_dump()))
    alert.status = payload.disposition
    alert.confirmed_threat_level = payload.threat_level
    record_audit(
        db,
        "ALERT_REVIEWED",
        "alert",
        alert_id,
        actor=payload.reviewer,
        metadata={"disposition": payload.disposition, "threat_level": payload.threat_level},
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
    review = PlanApplicabilityReview(alert_id=alert_id, **payload.model_dump())
    db.add(review)
    db.flush()
    record_audit(db, "PLAN_APPLICABILITY_REVIEWED", "alert", alert_id, metadata=payload.model_dump())
    db.commit()
    return {"id": review.id, "status": "recorded"}
