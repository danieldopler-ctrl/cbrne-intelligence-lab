from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.detection.ai_misuse_engine import run_ai_misuse_detection
from app.detection.engine import run_detection
from app.schemas.api import DetectionRequest, DetectionResult


router = APIRouter(prefix="/detections", tags=["detections"])


@router.post("/run", response_model=DetectionResult)
def execute_detection(payload: DetectionRequest, db: Session = Depends(get_db)) -> DetectionResult:
    if payload.domain_pack == "AI_MISUSE":
        run = run_ai_misuse_detection(db, payload.ingest_batch_id)
    else:
        run = run_detection(db, payload.ingest_batch_id, include_observations=payload.include_observations)
    return DetectionResult(
        detection_run_id=run.id,
        events_evaluated=run.event_count,
        alerts_created=run.alert_count,
        rule_set_version=run.rule_set_version,
    )
