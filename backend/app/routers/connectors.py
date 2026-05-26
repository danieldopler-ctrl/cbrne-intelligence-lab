import json

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.config import settings
from app.database import get_db
from app.ingestion.delimited_upload import as_float, as_int, hash_bytes, parse_records, raw_record_hash, store_raw_file
from app.ingestion.nrc_workbook import parse_nrc_workbook
from app.models import IngestBatch, NormalizedEvent, RawRecord, Source
from app.schemas.api import BioConnectorSyncResult, ConnectorSyncResult


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
NRC_SOURCE_NAME = "National Response Center Annual Incident Data"
NRC_SOURCE_URL = "https://nrc.uscg.mil/"
NRC_LIMITATIONS = (
    "NRC public workbooks contain initial, unvalidated incident data supplied during incident "
    "reporting. Data may be incomplete, inaccurate, or later revised. Numeric consequence fields "
    "are report-level values and are not multiplied across material rows. Records support "
    "analyst triage and correlation; they do not establish malicious intent or validated cause."
)
CDC_NNDSS_SOURCE_NAME = "CDC NNDSS Weekly Data"
CDC_NNDSS_API_URL = "https://data.cdc.gov/resource/x9gk-5huc.json"
CDC_NNDSS_LIMITATIONS = (
    "CDC NNDSS weekly data are provisional reported counts subject to revision and delayed "
    "reporting. A weekly count above a published comparison value supports analyst review only; "
    "it does not establish cause, deliberate release, malicious intent, or an emergency."
)
WHO_DON_SOURCE_NAME = "WHO Disease Outbreak News"
WHO_DON_API_URL = "https://www.who.int/api/news/diseaseoutbreaknews"
WHO_DON_LIMITATIONS = (
    "WHO Disease Outbreak News provides selected official public-health event reports and is not "
    "an exhaustive inventory. A public report supports analyst context only and does not establish "
    "deliberate release, malicious intent, or attribution."
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


def optional_number(value: object) -> float | None:
    value_text = str(value or "").strip()
    if not value_text:
        return None
    try:
        return float(value_text.replace(",", ""))
    except ValueError:
        return None


def existing_source_event(db: Session, source_id: int, source_record_id: str) -> NormalizedEvent | None:
    return db.scalar(
        select(NormalizedEvent).where(
            NormalizedEvent.source_id == source_id,
            NormalizedEvent.source_record_id == source_record_id,
        )
    )


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


def get_or_create_nrc_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == NRC_SOURCE_NAME))
    if source:
        source.limitations = NRC_LIMITATIONS
        return source
    source = Source(
        name=NRC_SOURCE_NAME,
        organization="U.S. Coast Guard National Response Center",
        url=NRC_SOURCE_URL,
        source_type="PUBLIC_OFFICIAL_XLSX",
        modality="CHEM",
        access_terms="Public incident data workbook released through the NRC FOIA data portal.",
        limitations=NRC_LIMITATIONS,
    )
    db.add(source)
    db.flush()
    record_audit(db, "SOURCE_REGISTERED", "source", source.id, actor="nrc_connector")
    return source


def get_or_create_cdc_nndss_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == CDC_NNDSS_SOURCE_NAME))
    if source:
        source.limitations = CDC_NNDSS_LIMITATIONS
        return source
    source = Source(
        name=CDC_NNDSS_SOURCE_NAME,
        organization="Centers for Disease Control and Prevention",
        url="https://data.cdc.gov/NNDSS/NNDSS-Weekly-Data/x9gk-5huc",
        source_type="PUBLIC_OFFICIAL_API",
        modality="BIO",
        access_terms="Public CDC data catalog dataset accessed through the official Socrata API.",
        limitations=CDC_NNDSS_LIMITATIONS,
    )
    db.add(source)
    db.flush()
    record_audit(db, "SOURCE_REGISTERED", "source", source.id, actor="cdc_nndss_connector")
    return source


def get_or_create_who_don_source(db: Session) -> Source:
    source = db.scalar(select(Source).where(Source.name == WHO_DON_SOURCE_NAME))
    if source:
        source.limitations = WHO_DON_LIMITATIONS
        return source
    source = Source(
        name=WHO_DON_SOURCE_NAME,
        organization="World Health Organization",
        url=WHO_DON_API_URL,
        source_type="PUBLIC_OFFICIAL_API",
        modality="BIO",
        access_terms="Public WHO Disease Outbreak News resource accessed through the official API.",
        limitations=WHO_DON_LIMITATIONS,
    )
    db.add(source)
    db.flush()
    record_audit(db, "SOURCE_REGISTERED", "source", source.id, actor="who_don_connector")
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


@router.post("/nrc/import", response_model=ConnectorSyncResult, status_code=201)
async def import_nrc_workbook(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ConnectorSyncResult:
    filename = file.filename or "nrc-annual-incident-data.xlsx"
    if not filename.casefold().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="NRC import requires the official XLSX workbook format.")
    content = await file.read()
    try:
        records, headers = parse_nrc_workbook(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    source = get_or_create_nrc_source(db)
    stored_path = store_raw_file(settings.data_dir / "raw", filename, content)
    batch = IngestBatch(
        source_id=source.id,
        original_filename=filename,
        stored_path=str(stored_path),
        sha256=hash_bytes(content),
        record_count=len(records),
        mapping_version="nrc-cy-workbook-v1",
        status="NORMALIZED",
    )
    db.add(batch)
    db.flush()
    material_rows = 0
    chemical_events = 0
    for record in records:
        source_rows = record["source_rows"]
        material_rows += len(source_rows["materials"])
        raw = RawRecord(
            ingest_batch_id=batch.id,
            source_record_id=record["report_id"],
            payload=source_rows,
            raw_hash=raw_record_hash(source_rows),
        )
        db.add(raw)
        db.flush()
        hazard_domain = "CHEM" if record["commodities"] else "OTHER"
        if hazard_domain == "CHEM":
            chemical_events += 1
        db.add(
            NormalizedEvent(
                source_id=source.id,
                ingest_batch_id=batch.id,
                raw_record_id=raw.id,
                source_record_id=record["report_id"],
                event_date=record["event_date"],
                reported_date=None,
                hazard_domain=hazard_domain,
                event_type="reported environmental release",
                region=record["region"],
                commodity=record["commodity"],
                severity_features=record["severity_features"],
                narrative=record["narrative"],
                source_url=source.url,
                data_classification="PUBLIC",
                limitations=NRC_LIMITATIONS,
            )
        )
    record_audit(
        db,
        "OFFICIAL_EXPORT_IMPORTED",
        "ingest_batch",
        batch.id,
        actor="nrc_connector",
        metadata={
            "source": NRC_SOURCE_NAME,
            "reports": len(records),
            "material_rows": material_rows,
            "chemical_events": chemical_events,
            "worksheet_headers": headers,
        },
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


@router.post("/cdc-nndss/sync", response_model=BioConnectorSyncResult, status_code=201)
def sync_cdc_nndss(
    year: int = Query(..., ge=2014, le=2100),
    week: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db),
) -> BioConnectorSyncResult:
    query_params = {
        "$where": f"year = '{year}' AND week = '{week}'",
        "$order": "sort_order ASC",
        "$limit": "10000",
    }
    try:
        response = httpx.get(CDC_NNDSS_API_URL, params=query_params, timeout=45.0, follow_redirects=True)
        response.raise_for_status()
        records = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="CDC NNDSS weekly feed could not be retrieved.") from exc
    if not isinstance(records, list):
        raise HTTPException(status_code=502, detail="CDC NNDSS response was not a JSON record collection.")
    records = [
        row
        for row in records
        if str(row.get("year") or "") == str(year) and str(row.get("week") or "") == str(week)
    ]
    if len(records) >= 10000:
        raise HTTPException(
            status_code=409,
            detail="CDC NNDSS reporting-week query reached the import cap; narrow scope before processing.",
        )
    content = json.dumps(records, sort_keys=True, default=str).encode()
    source = get_or_create_cdc_nndss_source(db)
    stored_path = store_raw_file(settings.data_dir / "raw", f"cdc-nndss-{year}-w{week:02d}.json", content)
    batch = IngestBatch(
        source_id=source.id,
        original_filename=f"cdc-nndss-{year}-w{week:02d}.json",
        stored_path=str(stored_path),
        sha256=hash_bytes(content),
        record_count=len(records),
        mapping_version="cdc-nndss-weekly-v1",
        status="NORMALIZED",
    )
    db.add(batch)
    db.flush()
    existing_cdc_hashes = dict(
        db.execute(
            select(NormalizedEvent.source_record_id, RawRecord.raw_hash)
            .join(RawRecord, NormalizedEvent.raw_record_id == RawRecord.id)
            .where(
                NormalizedEvent.source_id == source.id,
                NormalizedEvent.hazard_domain == "BIO",
            )
        ).all()
    )
    created = 0
    duplicates = 0
    revised = 0
    non_scorable = 0
    for row in records:
        identity = "|".join(
            str(row.get(field) or "")
            for field in ("year", "week", "states", "label", "sort_order")
        )
        base_record_id = f"CDC-NNDSS-{hash_bytes(identity.encode())[:24]}"
        row_hash = raw_record_hash(row)
        source_record_id = base_record_id
        if base_record_id in existing_cdc_hashes:
            if existing_cdc_hashes[base_record_id] == row_hash:
                duplicates += 1
                continue
            else:
                source_record_id = f"{base_record_id}-REV-{row_hash[:12]}"
                if source_record_id in existing_cdc_hashes:
                    duplicates += 1
                    continue
                else:
                    revised += 1
        raw = RawRecord(
            ingest_batch_id=batch.id,
            source_record_id=source_record_id,
            payload=row,
            raw_hash=row_hash,
        )
        db.add(raw)
        db.flush()
        flags = {
            "current_week_flag": row.get("m1_flag"),
            "previous_52_week_max_flag": row.get("m2_flag"),
            "cumulative_current_ytd_flag": row.get("m3_flag"),
            "cumulative_previous_ytd_flag": row.get("m4_flag"),
        }
        current_week = optional_number(row.get("m1"))
        previous_max = optional_number(row.get("m2"))
        scorable = current_week is not None and previous_max is not None and not any(
            str(flag or "").strip() for flag in (row.get("m1_flag"), row.get("m2_flag"))
        )
        if not scorable:
            non_scorable += 1
        features = {
            "source_system": "CDC_NNDSS",
            "data_status": "PROVISIONAL",
            "mmwr_year": row.get("year") or str(year),
            "mmwr_week": row.get("week") or str(week),
            "reporting_area": row.get("states"),
            "condition_label": row.get("label"),
            "current_week_count": current_week,
            "previous_52_week_max": previous_max,
            "cumulative_current_ytd": optional_number(row.get("m3")),
            "cumulative_previous_ytd": optional_number(row.get("m4")),
            "location1": row.get("location1"),
            "location2": row.get("location2"),
            "sort_order": row.get("sort_order"),
            "source_flags": flags,
            "scorable": scorable,
            "source_record_identity": base_record_id,
            "revision_of": base_record_id if source_record_id != base_record_id else None,
        }
        db.add(
            NormalizedEvent(
                source_id=source.id,
                ingest_batch_id=batch.id,
                raw_record_id=raw.id,
                source_record_id=source_record_id,
                event_date=f"{year}-W{week:02d}",
                reported_date=f"{year}-W{week:02d}",
                hazard_domain="BIO",
                event_type="public health surveillance report",
                region=str(row.get("states") or "") or None,
                commodity=str(row.get("label") or "") or None,
                severity_features=features,
                narrative=None,
                source_url=source.url,
                data_classification="PUBLIC",
                limitations=CDC_NNDSS_LIMITATIONS,
            )
        )
        existing_cdc_hashes[source_record_id] = row_hash
        created += 1
    record_audit(
        db,
        "OFFICIAL_CONNECTOR_SYNCED",
        "ingest_batch",
        batch.id,
        actor="cdc_nndss_connector",
        metadata={
            "source": CDC_NNDSS_SOURCE_NAME,
            "year": year,
            "week": week,
            "records": len(records),
            "events_created": created,
            "duplicate_records": duplicates,
            "revised_records": revised,
            "non_scorable_records": non_scorable,
        },
    )
    db.commit()
    return BioConnectorSyncResult(
        source_id=source.id,
        ingest_batch_id=batch.id,
        records_received=len(records),
        bio_events=created,
        duplicate_records=duplicates,
        revised_records=revised,
        non_scorable_records=non_scorable,
        sha256=batch.sha256,
        mapping_version=batch.mapping_version,
        limitation=CDC_NNDSS_LIMITATIONS,
    )


@router.post("/who-don/sync", response_model=BioConnectorSyncResult, status_code=201)
def sync_who_don(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BioConnectorSyncResult:
    query_params = {"$orderby": "PublicationDateAndTime desc", "$top": str(limit)}
    try:
        response = httpx.get(WHO_DON_API_URL, params=query_params, timeout=45.0, follow_redirects=True)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="WHO Disease Outbreak News feed could not be retrieved.") from exc
    records = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise HTTPException(status_code=502, detail="WHO Disease Outbreak News response was not a JSON record collection.")
    records = records[:limit]
    content = json.dumps(records, sort_keys=True, default=str).encode()
    source = get_or_create_who_don_source(db)
    stored_path = store_raw_file(settings.data_dir / "raw", f"who-don-latest-{limit}.json", content)
    batch = IngestBatch(
        source_id=source.id,
        original_filename=f"who-don-latest-{limit}.json",
        stored_path=str(stored_path),
        sha256=hash_bytes(content),
        record_count=len(records),
        mapping_version="who-don-api-v1",
        status="NORMALIZED",
    )
    db.add(batch)
    db.flush()
    created = 0
    duplicates = 0
    for index, row in enumerate(records, start=1):
        source_record_id = str(
            row.get("DonId")
            or f"WHO-DON-{hash_bytes(str(row.get('ItemDefaultUrl') or index).encode())[:24]}"
        )
        raw = RawRecord(
            ingest_batch_id=batch.id,
            source_record_id=source_record_id,
            payload=row,
            raw_hash=raw_record_hash(row),
        )
        db.add(raw)
        db.flush()
        if existing_source_event(db, source.id, source_record_id):
            duplicates += 1
            continue
        publication = str(row.get("PublicationDateAndTime") or "")
        report_url = str(row.get("ItemDefaultUrl") or source.url)
        db.add(
            NormalizedEvent(
                source_id=source.id,
                ingest_batch_id=batch.id,
                raw_record_id=raw.id,
                source_record_id=source_record_id,
                event_date=publication[:10] or None,
                reported_date=publication[:10] or None,
                hazard_domain="BIO",
                event_type="official outbreak report",
                region=None,
                commodity=None,
                severity_features={
                    "source_system": "WHO_DON",
                    "don_id": row.get("DonId"),
                    "title": row.get("Title"),
                    "publication_date_time": row.get("PublicationDateAndTime"),
                    "official_report_url": report_url,
                    "provider": row.get("Provider"),
                },
                narrative=row.get("Summary"),
                source_url=report_url,
                data_classification="PUBLIC",
                limitations=WHO_DON_LIMITATIONS,
            )
        )
        created += 1
    record_audit(
        db,
        "OFFICIAL_CONNECTOR_SYNCED",
        "ingest_batch",
        batch.id,
        actor="who_don_connector",
        metadata={
            "source": WHO_DON_SOURCE_NAME,
            "requested_limit": limit,
            "records": len(records),
            "events_created": created,
            "duplicate_records": duplicates,
        },
    )
    db.commit()
    return BioConnectorSyncResult(
        source_id=source.id,
        ingest_batch_id=batch.id,
        records_received=len(records),
        bio_events=created,
        duplicate_records=duplicates,
        sha256=batch.sha256,
        mapping_version=batch.mapping_version,
        limitation=WHO_DON_LIMITATIONS,
    )
