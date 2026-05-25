from sqlalchemy import select

from app.database import SessionLocal
from app.models import IngestBatch, NormalizedEvent, RawRecord, Source
from app.routers.connectors import PHMSA_LIMITATIONS, PHMSA_SOURCE_NAME, phmsa_severity_features


def main() -> None:
    updated_events = 0
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.name == PHMSA_SOURCE_NAME))
        if not source:
            print("No PHMSA source was found.")
            return
        source.limitations = PHMSA_LIMITATIONS
        rows = db.execute(
            select(NormalizedEvent, RawRecord)
            .join(RawRecord, RawRecord.id == NormalizedEvent.raw_record_id)
            .where(NormalizedEvent.source_id == source.id)
        ).all()
        batch_ids: set[int] = set()
        for event, raw in rows:
            event.severity_features = phmsa_severity_features(raw.payload or {})
            event.limitations = PHMSA_LIMITATIONS
            batch_ids.add(event.ingest_batch_id)
            updated_events += 1
        for batch_id in batch_ids:
            batch = db.get(IngestBatch, batch_id)
            if batch:
                batch.mapping_version = "phmsa-hazmat-export-v3-stage2-backfill"
        db.commit()
    print(
        f"Updated Stage 2 PHMSA features for {updated_events} normalized events "
        f"across {len(batch_ids)} ingest batch(es)."
    )


if __name__ == "__main__":
    main()
