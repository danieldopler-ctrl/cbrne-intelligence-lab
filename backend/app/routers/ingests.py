from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.config import settings
from app.database import get_db
from app.ingestion.delimited_upload import (
    map_severity_features,
    mapped_value,
    parse_records,
    raw_record_hash,
    store_raw_file,
    hash_bytes,
)
from app.models import IngestBatch, NormalizedEvent, RawRecord, Source
from app.schemas.api import IngestOut, MappingRequest, NormalizationResult


router = APIRouter(prefix="/ingests", tags=["ingests"])


@router.post("/upload", response_model=IngestOut, status_code=201)
async def upload_extract(
    source_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestBatch:
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source must be registered before ingestion.")
    content = await file.read()
    filename = file.filename or "uploaded.csv"
    try:
        records = parse_records(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    stored_path = store_raw_file(settings.data_dir / "raw", filename, content)
    batch = IngestBatch(
        source_id=source_id,
        original_filename=Path(filename).name,
        stored_path=str(stored_path),
        sha256=hash_bytes(content),
        record_count=len(records),
        status="UPLOADED",
    )
    db.add(batch)
    db.flush()
    for index, record in enumerate(records, start=1):
        source_record_id = str(record.get("id") or record.get("incident_id") or index)
        db.add(
            RawRecord(
                ingest_batch_id=batch.id,
                source_record_id=source_record_id,
                payload=record,
                raw_hash=raw_record_hash(record),
            )
        )
    record_audit(db, "INGEST_UPLOADED", "ingest_batch", batch.id, metadata={"records": len(records)})
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/{batch_id}", response_model=IngestOut)
def get_ingest(batch_id: int, db: Session = Depends(get_db)) -> IngestBatch:
    batch = db.get(IngestBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Ingest batch not found.")
    return batch


@router.post("/{batch_id}/normalize", response_model=NormalizationResult)
def normalize_ingest(
    batch_id: int, payload: MappingRequest, db: Session = Depends(get_db)
) -> NormalizationResult:
    batch = db.get(IngestBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Ingest batch not found.")
    source = db.get(Source, batch.source_id)
    existing = db.scalar(
        select(NormalizedEvent.id).where(NormalizedEvent.ingest_batch_id == batch_id).limit(1)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Batch was already normalized.")
    raw_records = db.scalars(
        select(RawRecord).where(RawRecord.ingest_batch_id == batch_id).order_by(RawRecord.id)
    ).all()
    for raw in raw_records:
        row = raw.payload
        db.add(
            NormalizedEvent(
                source_id=batch.source_id,
                ingest_batch_id=batch.id,
                raw_record_id=raw.id,
                source_record_id=str(
                    mapped_value(row, payload.fields, "source_record_id") or raw.source_record_id
                ),
                event_date=mapped_value(row, payload.fields, "event_date"),
                reported_date=mapped_value(row, payload.fields, "reported_date"),
                hazard_domain=str(
                    mapped_value(row, payload.fields, "hazard_domain") or payload.hazard_domain
                ).upper(),
                event_type=str(
                    mapped_value(row, payload.fields, "event_type") or payload.event_type_default
                ),
                region=mapped_value(row, payload.fields, "region"),
                commodity=mapped_value(row, payload.fields, "commodity"),
                severity_features=map_severity_features(row, payload.fields),
                narrative=mapped_value(row, payload.fields, "narrative"),
                source_url=mapped_value(row, payload.fields, "source_url") or (source.url if source else None),
                data_classification=payload.data_classification,
                limitations=source.limitations if source else "Source limitations not registered.",
            )
        )
    batch.status = "NORMALIZED"
    batch.mapping_version = payload.version
    record_audit(db, "INGEST_NORMALIZED", "ingest_batch", batch.id, metadata=payload.model_dump())
    db.commit()
    return NormalizationResult(
        ingest_batch_id=batch.id,
        records_processed=len(raw_records),
        events_created=len(raw_records),
        mapping_version=payload.version,
    )
