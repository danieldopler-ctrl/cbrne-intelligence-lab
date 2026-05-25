from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NormalizedEvent
from app.schemas.api import EventOut


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(
    domain: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[NormalizedEvent]:
    query = select(NormalizedEvent).order_by(NormalizedEvent.id.desc()).limit(limit)
    if domain:
        query = (
            select(NormalizedEvent)
            .where(NormalizedEvent.hazard_domain == domain.upper())
            .order_by(NormalizedEvent.id.desc())
            .limit(limit)
        )
    return list(db.scalars(query).all())


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> NormalizedEvent:
    event = db.get(NormalizedEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event
