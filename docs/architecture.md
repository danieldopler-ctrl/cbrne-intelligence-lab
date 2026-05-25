# Architecture

## Operational Flow

```text
Registered official or approved source
  -> immutable local raw snapshot and SHA-256 hash
  -> analyst-approved field mapping
  -> normalized event table
  -> versioned CBRN-E domain rules
  -> indicators and alerts with linked source evidence
  -> analyst review and threat-level confirmation
  -> notification and response-doctrine audit workflow
  -> evaluation and reviewed reporting (later stage)
```

## Separation Of Concerns

| Component | Owns |
|---|---|
| Platform core | Sources, ingests, normalized events, alerts, reviews, notifications, audit |
| Domain pack | Taxonomy, detection rules, thresholds, evidence expectations |
| Analyst | Confirmation, disposition, escalation, reporting decision |
| Responsible agency/jurisdiction | Emergency action, formal reporting, incident command, plan activation |

## Initial Services

| Service | Stage 1 capability |
|---|---|
| API | FastAPI routes for core workflow |
| Database | PostgreSQL schema managed through Alembic |
| Ingestion | CSV/JSON upload plus source-field mapping |
| Detection | Versioned CHEM/hazmat rule execution |
| Review | Alert disposition, threat level, notification assessment, plan mapping |
| Interface | Next.js operational dashboard |

## AI Misuse Assessment Boundary

The `AI_MISUSE` pack reuses provenance, alerts, review, evaluation, and audit storage, while
separating safety-review routing from field-incident handling. Its controlled fixtures use
`AI_MISUSE_REVIEW` with `MR0` through `MR3`. API enforcement prevents those records from opening
external notification or response-doctrine actions.

## Growth Path

NOAA, PHMSA, and NRC connectors provide CHEM/hazmat source records after format verification. NRC reports are joined across official workbook sheets by `SEQNOS` and can be compared with PHMSA reports for analyst-reviewed correlation. WHO DON and CDC NNDSS connectors can later extend monitoring into BIO. Fraud or another risk domain later adds new event fields and rules while retaining the platform workflow.

The AI Misuse Risk Assessment Module is implemented before BIO expansion as a controlled safety
analysis increment relevant to AI safety investigation. It is not a live model testing system.
