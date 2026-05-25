from sqlalchemy import select

from app.database import SessionLocal
from app.models import NormalizedEvent, RawRecord


def main() -> None:
    updated = 0
    with SessionLocal() as db:
        events = db.execute(
            select(NormalizedEvent, RawRecord)
            .join(RawRecord, RawRecord.id == NormalizedEvent.raw_record_id)
            .where(NormalizedEvent.commodity.is_(None))
        ).all()
        for event, raw in events:
            commodity = (raw.payload or {}).get("commodity")
            if commodity:
                event.commodity = str(commodity)
                updated += 1
        db.commit()
    print(f"Backfilled commodity for {updated} normalized events.")


if __name__ == "__main__":
    main()
