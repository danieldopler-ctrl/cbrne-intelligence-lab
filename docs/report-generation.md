# Source-Cited Report Generation

## Purpose

Stage 7 turns completed analyst reviews into deterministic, exportable records. A report records
which alert was reviewed, what rule rationale was already stored, which source evidence supports
the alert, what source limits apply, and what disposition the analyst recorded.

It does not add conclusions, change recorded review levels, transmit a report, or call an AI
service.

## Workflow

```text
Reviewed alert(s) in one domain pack and rule-set version
  -> analyst selects records and supplies a report title
  -> platform displays the applicable domain disclosure
  -> deterministic report record is stored
  -> analyst may view, download JSON, or print HTML
```

## Controls

| Control | Behavior |
|---|---|
| Review gate | Any alert without an analyst review record is rejected from reporting. |
| Domain isolation | CHEM, BIO, AI misuse, and fraud fixture alerts cannot appear together in one report. |
| Version isolation | Alerts generated under separate rule-set versions cannot appear together. |
| Citation preservation | The report retains existing source URLs/references and source limitations. |
| Disclosure | Each domain pack uses a fixed statement of what its report cannot establish. |
| Delivery | No automatic send, notification, or publication is implemented. |
| AI text | No AI API request or generated narrative is implemented. |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /reports` | List generated reports; optional `domain_pack` filter. |
| `GET /reports/eligible-alerts?domain_pack=...` | List reviewed alerts available for reporting. |
| `POST /reports/generate` | Persist one source-cited report from reviewed alerts. |
| `GET /reports/{id}` | Retrieve the stored report payload. |
| `GET /reports/{id}/export.json` | Download the stored deterministic JSON payload. |

## Display Notes

The report detail view puts the domain disclosure at the top and presents evidence beneath each
reviewed alert. For CDC NNDSS evidence, the view repeats that counts are provisional and subject
to revision. AI misuse reports display MR review levels separately from TL incident-review
levels and remain fixture-conformance records only. Fraud reports display FR review levels and
remain controlled synthetic-fixture conformance records only.
