# CBRN-E Intelligence Lab

CBRN-E Intelligence Lab is a real-data risk signal platform under development. It ingests approved public or user-provided datasets, normalizes source records, runs explainable detection rules, and creates evidence-linked alerts for analyst review.

CBRN-E is the first domain pack. The platform core is designed so a later approved domain pack, such as fraud or supply-chain risk, can reuse ingestion, alerts, reviews, evaluation, and audit history while providing its own data model and detection logic.

## Current Build Status

Stage 1 foundation is in progress:

- PostgreSQL-backed application model and migration.
- FastAPI endpoints for sources, ingestion, normalized events, detection runs, alerts, analyst reviews, notifications, and response-doctrine review.
- Next.js analyst interface for source registration, dataset upload, and alert review.
- Direct NOAA IncidentNews public-domain CSV connector for selected response-support incidents.
- Initial CHEM/hazmat rule set intended for NOAA records and later PHMSA or NRC-formatted public records after field mapping.

This build does **not** confirm malicious intent and does **not** automatically notify external agencies. Automated detections are review priorities.

## Stack

| Layer | Technology |
|---|---|
| API | Python, FastAPI, Pydantic |
| Data access | SQLAlchemy, Alembic |
| Operational database | PostgreSQL |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Local service orchestration | Docker Compose |
| Testing | Pytest, FastAPI TestClient |

## Run Locally

Prerequisites: Python 3.12+, `uv`, Node.js, and PostgreSQL or Docker.

With a local PostgreSQL service, create a database and use the local socket connection:

```bash
cp .env.example .env
/opt/homebrew/opt/postgresql@16/bin/createdb cbrne_lab
# Set DATABASE_URL=postgresql+psycopg:///cbrne_lab in .env
cd backend
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Docker Compose remains an alternative where Docker is available:

```bash
docker compose up -d postgres
# Keep the DATABASE_URL value provided in .env.example
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The API health endpoint is `http://localhost:8000/health`.

## Source Handling

Stage 0 source candidates are official public data:

| Source | Intended use |
|---|---|
| NOAA IncidentNews Raw Incident Data | First direct public-domain CHEM incident connector |
| PHMSA Hazmat Incident Reports | CHEM/hazmat incident analysis and baselines |
| National Response Center reports | Environmental release event monitoring |
| WHO Disease Outbreak News API | BIO report ingestion in a later increment |
| CDC NNDSS Weekly Data | BIO baseline analysis in a later increment |

Raw data files are local-only and excluded from git. Each ingest records source metadata, file hash, mapping version, and limitations. NOAA IncidentNews contains selected incidents where NOAA supported response; it is not a complete inventory and cannot establish malicious intent.

NOAA commodity names are normalized into a dedicated event field. `CHEM-SUBSTANCE-001` compares that field to the EPA RMP regulated toxic substances in `40 CFR 68.130 Table 1` and creates an analyst review item for a documented match. The signal does not identify malicious intent, regulatory applicability, or verified consequences.

PHMSA delimited-text exports can be imported from the Sources screen. The importer maps `Total Hazmat Fatalities` as a numeric count and converts `Hazmat Injury Indicator` and `Serious Evacuations` values of `Yes` to `TL2` reported-consequence signals for `CHEM-CONSEQUENCE-001`; the indicators are not counts. Stage 2 uses `Report Number` to avoid duplicate incident-level consequence alerts and applies `CHEM-RELEASE-QUANTITY-001` only to quantities reported by PHMSA as standardized liquid gallons (`LGA`). `GCF` and `SLB` data remain preserved without conversion.

The dashboard and default alert queue display the latest detection run so historical calibration runs are not added into current alert totals. Earlier runs remain stored for audit review.

## Threat And Escalation Handling

Alerts use `TL0` through `TL4` handling:

| Level | Meaning |
|---|---|
| `TL0` | Logged observation |
| `TL1` | Monitor |
| `TL2` | Investigate with senior review |
| `TL3` | Escalate for internal notification and external-report assessment |
| `TL4` | Emergency or mandatory-report condition; software workflow must not delay response |

For `TL3` and `TL4`, the platform records possible applicability of `NIMS/ICS`, `NRF`/ESFs, `NCP/NRS`, `BIA`, `NRIA`, or narrowly scoped `NARP` references. It cannot claim a responsible agency activated a plan unless verified evidence is recorded.

## Documentation

- [Architecture](docs/architecture.md)
- [Source Manifest](docs/source-manifest.md)
- [Detection Methodology](docs/detection-methodology.md)
- [Safety and Data Governance](docs/safety-data-governance.md)
- [Escalation and Notification Matrix](docs/escalation-and-notification-matrix.md)
- [Response Doctrine Mapping](docs/response-doctrine-mapping.md)
- [Domain Pack Design](docs/domain-pack-design.md)

## Roadmap

| Stage | Objective | Status |
|---|---|---|
| Stage 0 | Verify initial public sources and common schema | In progress |
| Stage 1 | Real data ingestion and evidence-linked CHEM alerts | In progress |
| Stage 2 | Chemical/hazmat backtesting and review metrics | Planned |
| Stage 3 | WHO/CDC BIO monitoring connectors | Planned |
| Stage 4 | Evaluation reports and evidence-constrained AI summaries | Planned |
| Stage 5 | Domain expansion and deployment decision | Planned |

## Purpose And Limits

This project is built with AI assistance as part of Daniel Dopler's development of an operationally serious risk-analysis platform and technical portfolio. The system supports defensible review of evidence; it is not a substitute for emergency response, reporting obligations, or authorized investigation.
