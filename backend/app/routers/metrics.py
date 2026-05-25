from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, DetectionRun, IngestBatch, NormalizedEvent, Source


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
def metrics_summary(db: Session = Depends(get_db)) -> dict[str, int | str | None]:
    latest_run = db.scalar(select(DetectionRun).order_by(DetectionRun.id.desc()).limit(1))
    current_run_open_alerts = 0
    if latest_run:
        current_run_open_alerts = (
            db.scalar(
                select(func.count(Alert.id)).where(
                    Alert.detection_run_id == latest_run.id,
                    Alert.status == "NEW",
                )
            )
            or 0
        )
    return {
        "sources": db.scalar(select(func.count(Source.id))) or 0,
        "ingest_batches": db.scalar(select(func.count(IngestBatch.id))) or 0,
        "events": db.scalar(select(func.count(NormalizedEvent.id))) or 0,
        "open_alerts": current_run_open_alerts,
        "current_detection_run_id": latest_run.id if latest_run else None,
        "current_rule_set_version": latest_run.rule_set_version if latest_run else None,
    }
