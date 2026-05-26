from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, AnalystReview, DetectionRun, Report
from app.reporting.service import create_report_payload
from app.schemas.api import ReportGenerateRequest


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_reports(
    domain_pack: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    query = select(Report).order_by(Report.id.desc())
    if domain_pack:
        query = query.where(Report.domain_pack == domain_pack)
    return [
        {
            "id": report.id,
            "title": report.title,
            "domain_pack": report.domain_pack,
            "rule_set_version": report.rule_set_version,
            "alert_count": len(report.alert_ids),
            "generated_at": report.generated_at,
        }
        for report in db.scalars(query).all()
    ]


@router.get("/eligible-alerts")
def list_eligible_alerts(
    domain_pack: str,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    rows = db.execute(
        select(Alert, DetectionRun)
        .join(DetectionRun, Alert.detection_run_id == DetectionRun.id)
        .where(DetectionRun.domain_pack == domain_pack)
        .order_by(Alert.created_at.desc())
    ).all()
    results: list[dict[str, object]] = []
    for alert, run in rows:
        review = db.scalar(
            select(AnalystReview)
            .where(AnalystReview.alert_id == alert.id)
            .order_by(AnalystReview.id.desc())
            .limit(1)
        )
        if review:
            results.append(
                {
                    "id": alert.id,
                    "title": alert.title,
                    "domain_pack": run.domain_pack,
                    "rule_set_version": run.rule_set_version,
                    "review_framework": alert.review_framework,
                    "review_level": review.review_level or review.threat_level,
                    "disposition": review.disposition,
                    "reviewed_at": review.reviewed_at,
                }
            )
    return results


@router.post("/generate", status_code=201)
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return create_report_payload(db, payload.title, payload.alert_ids)


@router.get("/{report_id}/export.json")
def export_report(report_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return JSONResponse(
        content=report.report_data,
        headers={"Content-Disposition": f'attachment; filename="report-{report.id}.json"'},
    )


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report.report_data
