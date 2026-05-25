import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.config import settings
from app.database import get_db
from app.ingestion.delimited_upload import as_float, as_int, hash_bytes, parse_records, raw_record_hash, store_raw_file
from app.models import IngestBatch, NormalizedEvent, RawRecord, Source
from app.schemas.api import ConnectorSyncResult


router = APIRouter(prefix="/connectors", tags=["connectors"])

NOAA_SOURCE_NAME = "NOAA IncidentNews Raw Incident Data"
NOAA_CSV_URL = "https://incidentnews.noaa.gov/raw/incidents.csv"
NOAA_LIMITATIONS = (
    "Selected incidents where NOAA OR&R provided scientific support; the dataset is not a "
    "complete inventory of releases and does not establish malicious intent. Maximum potential "
    "release is not necessarily actual release."
)
PHMSA_SOURCE_NAME = "PHMSA Hazmat Incident Reports - Data Mining Tool"
PHMSA_SOURCE_URL = (
    "https://www.phmsa.dot.gov/hazmat-program-management-data-and-statistics/"
    "data-operations/incident-statistics"
)
PHMSA_LIMITATIONS = (
    "DOT Form 5800.1 transportation incident records identify source-reported events and "
    "consequences, not malicious intent. Exports may include multiple rows for a single incident "
    "when multiple shippers, commodities, or packages are involved; analysts must check incident "
    "identity before aggregating alerts or consequences. Release quantities are scored only when "
    "PHMSA supplies standardized liquid gallons (`LGA`); gas cubic feet and solid pounds are "
    "preserved without gallon conversion."
)


def as_yes_indicator(value: object) -> int:
    return 1 if str(value or "").strip().casefold() == "yes" else 0


def phmsa_severity_features(row: dict[str, object]) -> dict[str, object]:
    unit = str(row.get("Unit Of Measure") or "").strip().upper()
    features: dict[str, object] = {
        "fatalities": as_int(row.get("Total Hazmat Fatalities")),
        "injuries": as_yes_indicator(row.get("Hazmat Injury Indicator")),
        "evacuated": as_yes_indicator(row.get("Serious Evacuations")),
        "consequence_basis": "binary_indicators_with_numeric_fatalities",
        "quantity_released_source": as_float(row.get("Quantity Released")),
        "quantity_unit": unit,
    }
    if unit == "LGA":
        features["quantity_released_liquid_gallons"] = as_float(row.get("Quantity Released"))
    return features


def get_or_create_noaa_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == NOAA_SOURCE_NAME))
    if source:
        return source
    source = Source(
        name=NOAA_SOURCE_NAME,
        organization="NOAA Office of Response and Restoration",
        url="https://incidentnews.noaa.gov/raw/index",
        source_type="PUBLIC_OFFICIAL_CSV",
        modality="CHEM",
        access_terms="Public domain; no copyright restriction stated by NOAA IncidentNews.",
        limitations=NOAA_LIMITATIONS,
    )
    db.add(source)
    db.flush()
    record_audit(db, "SOURCE_REGISTERED", "source", source.id, actor="noaa_connector")
    return source


def get_or_create_phmsa_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == PHMSA_SOURCE_NAME))
    if source:
        source.limitations = PHMSA_LIMITATIONS
        return source
    source = Source(
        name=PHMSA_SOURCE_NAME,
        organization="Pipeline and Hazardous Materials Safety Administration",
        url=PHMSA_SOURCE_URL,
        source_type="PUBLIC_OFFICIAL_EXPORT",
        modality="CHEM",
        access_terms="Public dataset; DOT catalog identifies the dataset as public domain.",
        limitations=PHMSA_LIMITATIONS,
    )
    db.add(source)
    db.flush()
    record_audit(db, "SOURCE_REGISTERED", "source", source.id, actor="phmsa_connector")
    return source


@router.post("/noaa-incidentnews/sync", response_model=ConnectorSyncResult, status_code=201)
def sync_noaa_incidentnews(db: Session = Depends(get_db)) -> ConnectorSyncResult:
    try:
        response = httpx.get(NOAA_CSV_URL, timeout=45.0, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="NOAA IncidentNews feed could not be retrieved.") from exc
    content = response.content
    records = parse_records("incidents.csv", content)
    source = get_or_create_noaa_source(db)
    stored_path = store_raw_file(settings.data_dir / "raw", "noaa-incidentnews-incidents.csv", content)
    batch = IngestBatch(
        source_id=source.id,
        original_filename="noaa-incidentnews-incidents.csv",
        stored_path=str(stored_path),
        sha256=hash_bytes(content),
        record_count=len(records),
        mapping_version="noaa-incidentnews-v2",
        status="NORMALIZED",
    )
    db.add(batch)
    db.flush()
    chemical_events = 0
    for index, row in enumerate(records, start=1):
        raw = RawRecord(
            ingest_batch_id=batch.id,
            source_record_id=str(row.get("id") or index),
            payload=row,
            raw_hash=raw_record_hash(row),
        )
        db.add(raw)
        db.flush()
        threat = str(row.get("threat") or "Other")
        hazard_domain = "CHEM" if threat.casefold() == "chemical" else "OTHER"
        if hazard_domain == "CHEM":
            chemical_events += 1
        quantity = row.get("max_ptl_release_gallons")
        try:
            release_gallons = int(float(quantity)) if quantity else 0
        except ValueError:
            release_gallons = 0
        db.add(
            NormalizedEvent(
                source_id=source.id,
                ingest_batch_id=batch.id,
                raw_record_id=raw.id,
                source_record_id=raw.source_record_id,
                event_date=row.get("open_date"),
                reported_date=row.get("open_date"),
                hazard_domain=hazard_domain,
                event_type="chemical release" if hazard_domain == "CHEM" else f"{threat.lower()} incident",
                region=row.get("location"),
                commodity=row.get("commodity") or None,
                severity_features={"quantity_released": release_gallons},
                narrative=row.get("description"),
                source_url=source.url,
                data_classification="PUBLIC",
                limitations=NOAA_LIMITATIONS,
            )
        )
    record_audit(
        db,
        "OFFICIAL_CONNECTOR_SYNCED",
        "ingest_batch",
        batch.id,
        actor="noaa_connector",
        metadata={"source": NOAA_SOURCE_NAME, "records": len(records), "chemical_events": chemical_events},
    )
    db.commit()
    return ConnectorSyncResult(
        source_id=source.id,
        ingest_batch_id=batch.id,
        records_received=len(records),
        chemical_events=chemical_events,
        sha256=batch.sha256,
        mapping_version=batch.mapping_version,
    )


@router.post("/phmsa-hazmat/import", response_model=ConnectorSyncResult, status_code=201)
async def import_phmsa_hazmat_export(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ConnectorSyncResult:
    filename = file.filename or "phmsa-hazmat-export.txt"
    content = await file.read()
    try:
        records = parse_records(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    required_fields = {
        "Date Of Incident",
        "Commodity Long Name",
        "Total Hazmat Fatalities",
        "Hazmat Injury Indicator",
        "Serious Evacuations",
        "Quantity Released",
        "Unit Of Measure",
    }
    if not records or not required_fields.issubset(records[0]):
        raise HTTPException(
            status_code=400,
            detail="PHMSA export is missing official consequence or commodity columns.",
        )
    source = get_or_create_phmsa_source(db)
    stored_path = store_raw_file(settings.data_dir / "raw", filename, content)
    batch = IngestBatch(
        source_id=source.id,
        original_filename=filename,
        stored_path=str(stored_path),
        sha256=hash_bytes(content),
        record_count=len(records),
        mapping_version="phmsa-hazmat-export-v3",
        status="NORMALIZED",
    )
    db.add(batch)
    db.flush()
    for index, row in enumerate(records, start=1):
        source_record_id = str(
            row.get("Incident ID")
            or row.get("Incident Number")
            or row.get("Report Number")
            or f"PHMSA-{batch.id}-{index}"
        )
        raw = RawRecord(
            ingest_batch_id=batch.id,
            source_record_id=source_record_id,
            payload=row,
            raw_hash=raw_record_hash(row),
        )
        db.add(raw)
        db.flush()
        location = ", ".join(
            value for value in (row.get("Incident City"), row.get("Incident State")) if value
        )
        db.add(
            NormalizedEvent(
                source_id=source.id,
                ingest_batch_id=batch.id,
                raw_record_id=raw.id,
                source_record_id=source_record_id,
                event_date=row.get("Date Of Incident"),
                reported_date=None,
                hazard_domain="CHEM",
                event_type="hazmat transportation incident",
                region=location or None,
                commodity=row.get("Commodity Long Name") or row.get("Commodity Short Name") or None,
                severity_features=phmsa_severity_features(row),
                narrative=row.get("Description of Events"),
                source_url=source.url,
                data_classification="PUBLIC",
                limitations=PHMSA_LIMITATIONS,
            )
        )
    record_audit(
        db,
        "OFFICIAL_EXPORT_IMPORTED",
        "ingest_batch",
        batch.id,
        actor="phmsa_connector",
        metadata={"source": PHMSA_SOURCE_NAME, "records": len(records)},
    )
    db.commit()
    return ConnectorSyncResult(
        source_id=source.id,
        ingest_batch_id=batch.id,
        records_received=len(records),
        chemical_events=len(records),
        sha256=batch.sha256,
        mapping_version=batch.mapping_version,
    )
