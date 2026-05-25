from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, IngestBatch, NormalizedEvent, Source


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
def metrics_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    return {
        "sources": db.scalar(select(func.count(Source.id))) or 0,
        "ingest_batches": db.scalar(select(func.count(IngestBatch.id))) or 0,
        "events": db.scalar(select(func.count(NormalizedEvent.id))) or 0,
        "open_alerts": db.scalar(select(func.count(Alert.id)).where(Alert.status == "NEW")) or 0,
    }
