import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test-cbrne.db"
os.environ["DATA_DIR"] = "./test-data"

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.routers import connectors


client = TestClient(app)


def setup_module() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_detect_review_and_plan_audit() -> None:
    source = client.post(
        "/sources",
        json={
            "name": "Approved Hazmat Extract",
            "organization": "Test Fixture",
            "url": "https://example.test/source",
            "source_type": "PUBLIC_DATASET",
            "modality": "CHEM",
            "access_terms": "Safe fixture for automated testing.",
            "limitations": "This is a test fixture and not an operational source record.",
        },
    )
    assert source.status_code == 201
    source_id = source.json()["id"]
    fixture = (
        "incident_id,event_date,type,region,commodity,injuries,fatalities,evacuated,narrative\n"
        "TEST-001,2026-01-01,chemical release,Region A,Test Material,6,0,0,Safe test fixture\n"
        "TEST-002,2026-01-02,chemical release,Region A,Test Material,0,0,0,Safe test fixture\n"
        "TEST-003,2026-01-03,chemical release,Region A,Test Material,0,0,0,Safe test fixture\n"
    )
    upload = client.post(
        f"/ingests/upload?source_id={source_id}",
        files={"file": ("fixture.csv", fixture, "text/csv")},
    )
    assert upload.status_code == 201
    batch_id = upload.json()["id"]
    normalize = client.post(
        f"/ingests/{batch_id}/normalize",
        json={
            "version": "test-v1",
            "fields": {
                "source_record_id": "incident_id",
                "event_date": "event_date",
                "event_type": "type",
                "region": "region",
                "commodity": "commodity",
                "injuries": "injuries",
                "fatalities": "fatalities",
                "evacuated": "evacuated",
                "narrative": "narrative",
            },
            "hazard_domain": "CHEM",
        },
    )
    assert normalize.status_code == 200
    run = client.post("/detections/run", json={"ingest_batch_id": batch_id})
    assert run.status_code == 200
    assert run.json()["alerts_created"] >= 2
    alerts = client.get("/alerts").json()
    alert_id = alerts[0]["id"]
    review = client.post(
        f"/alerts/{alert_id}/reviews",
        json={
            "reviewer": "test_analyst",
            "disposition": "ESCALATE",
            "threat_level": "TL3",
            "note": "Test review only.",
        },
    )
    assert review.status_code == 200
    notification = client.post(
        f"/alerts/{alert_id}/notifications",
        json={
            "threat_level": "TL3",
            "route_type": "INTERNAL",
            "route_name": "Duty Lead",
            "reporting_assessment": "REVIEW_REQUIRED",
            "rationale": "Test notification record only.",
        },
    )
    assert notification.status_code == 201
    plan = client.post(
        f"/alerts/{alert_id}/plan-reviews",
        json={
            "plan_code": "NIMS_ICS",
            "applicability": "POTENTIALLY_APPLICABLE",
            "rationale": "Test doctrine record only.",
            "reviewer": "test_analyst",
        },
    )
    assert plan.status_code == 201
    detail = client.get(f"/alerts/{alert_id}").json()
    assert detail["confirmed_threat_level"] == "TL3"
    assert detail["notifications"][0]["reporting_assessment"] == "REVIEW_REQUIRED"
    assert detail["plan_reviews"][0]["activation_status"] == "NOT_VERIFIED"


def test_noaa_connector_normalizes_official_shape(monkeypatch) -> None:
    csv_content = (
        "id,open_date,name,location,threat,tags,commodity,max_ptl_release_gallons,description\n"
        "NOAA-TEST-1,2026-01-04,Safe connector fixture,Test Coast,Chemical,Pipeline,"
        "Chlorine Gas,100,Safe connector test only\n"
    ).encode()

    class FakeResponse:
        content = csv_content

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(connectors.httpx, "get", lambda *args, **kwargs: FakeResponse())
    response = client.post("/connectors/noaa-incidentnews/sync")
    assert response.status_code == 201
    assert response.json()["records_received"] == 1
    assert response.json()["chemical_events"] == 1
    events = client.get("/events?domain=CHEM").json()
    event = next(event for event in events if event["source_record_id"] == "NOAA-TEST-1")
    assert event["commodity"] == "Chlorine Gas"
    run = client.post("/detections/run", json={"ingest_batch_id": response.json()["ingest_batch_id"]})
    assert run.status_code == 200
    assert run.json()["rule_set_version"] == "CHEM_HAZMAT_V0.3"
    assert run.json()["alerts_created"] == 1
    alerts = client.get("/alerts").json()
    assert any("EPA RMP toxic substance commodity match: NOAA-TEST-1" in alert["title"] for alert in alerts)


def test_phmsa_export_maps_consequences_for_detection() -> None:
    fixture = (
        "Incident ID\tDate Of Incident\tIncident City\tIncident State\tCommodity Long Name\t"
        "Total Hazmat Fatalities\tHazmat Injury Indicator\tSerious Evacuations\tQuantity Released\tUnit Of Measure\t"
        "Description of Events\n"
        "PHMSA-TEST-1\t2026-01-05\tTest City\tMI\tTest Material\t0\tYes\tYes\t60000\tLGA\t"
        "Safe PHMSA fixture line one\n"
        "PHMSA-TEST-1\t2026-01-05\tTest City\tMI\tTest Material\t0\tYes\tYes\t60000\tLGA\t"
        "Safe PHMSA duplicate incident line\n"
        "PHMSA-TEST-GCF\t2026-01-06\tTest City\tMI\tTest Gas\t0\tNo\tNo\t1000000\tGCF\t"
        "Safe unconverted gas quantity line\n"
    )
    imported = client.post(
        "/connectors/phmsa-hazmat/import",
        files={"file": ("phmsa-fixture.txt", fixture, "text/plain")},
    )
    assert imported.status_code == 201
    assert imported.json()["mapping_version"] == "phmsa-hazmat-export-v3"
    events = client.get("/events?domain=CHEM").json()
    event = next(event for event in events if event["source_record_id"] == "PHMSA-TEST-1")
    assert event["commodity"] == "Test Material"
    assert event["event_date"] == "2026-01-05"
    assert event["severity_features"]["fatalities"] == 0
    assert event["severity_features"]["injuries"] == 1
    assert event["severity_features"]["evacuated"] == 1
    assert event["severity_features"]["quantity_released_liquid_gallons"] == 60000
    gas_event = next(event for event in events if event["source_record_id"] == "PHMSA-TEST-GCF")
    assert "quantity_released_liquid_gallons" not in gas_event["severity_features"]
    run = client.post("/detections/run", json={"ingest_batch_id": imported.json()["ingest_batch_id"]})
    assert run.status_code == 200
    assert run.json()["rule_set_version"] == "CHEM_HAZMAT_V0.3"
    assert run.json()["alerts_created"] == 2
    alerts = client.get("/alerts").json()
    consequence = next(alert for alert in alerts if alert["title"] == "Reported consequence severity: PHMSA-TEST-1")
    release = next(
        alert for alert in alerts if alert["title"] == "Large PHMSA liquid-gallon release quantity: PHMSA-TEST-1"
    )
    assert consequence["recommended_threat_level"] == "TL2"
    assert release["score"] == 70
    assert not any("NOAA-TEST-1" in alert["title"] for alert in alerts)
    history = client.get("/alerts?include_history=true").json()
    assert any("NOAA-TEST-1" in alert["title"] for alert in history)
    summary = client.get("/metrics/summary").json()
    assert summary["open_alerts"] == 2
    assert summary["current_rule_set_version"] == "CHEM_HAZMAT_V0.3"
