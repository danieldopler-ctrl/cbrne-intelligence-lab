# Portfolio Walkthrough

## What This Platform Is

CBRN-E Intelligence Lab is a local risk-signal workflow application. It imports approved public
records and controlled fixtures, applies visible rules, links alerts back to source evidence,
records analyst review, evaluates selected routing behavior, and exports cited reviewed reports.

## What It Is Not

It does not establish malicious intent, use classified information, run live AI completions,
contact outside agencies, or operate as a deployed production system. Synthetic fixtures test
workflow behavior only.

## Build Summary

| Stage | Built | Validated | Decision demonstrated |
|---|---|---|---|
| 1 | NOAA and PHMSA ingestion, alerts, review and doctrine audit | End-to-end CHEM workflow | Begin with sourced evidence and analyst review |
| 2 | PHMSA deduplication and unit-aware handling | Duplicate and unit tests | Do not treat presence indicators as counts |
| 3 | NRC workbook import and bounded CHEM correlation | Numeric consequence and correlation tests | Keep correlation additive and source-linked |
| 4 | AI misuse review fixture and MR routing | Fixture conformance | Keep safety review separate from incident escalation |
| 5 | Evaluation and comparison records | Versioned run tests | Measure selected routing behavior without inflated claims |
| 6 | WHO and CDC BIO monitoring | Bounded import and CDC revision tests | Treat provisional updates as revisions, not duplicates |
| 7 | Source-cited reviewed reports | Report gate, isolation, and export tests | Reports preserve evidence and limitations |
| 8 | Fraud fixture adapter and closeout records | FR route and isolation tests | Shared records support another domain with dedicated adapters |

## Domain Portability Demonstration

`FRAUD_MONITORING_V0.1` uses the existing source, ingest, normalized event, detection run,
evidence, alert, evaluation, report, and audit records. It adds synthetic input, deterministic
fraud-category rules, `FRAUD_REVIEW` levels, reporting disclosure text, and interface routing.
That is the honest portability claim: common workflow records are reusable; domain logic and
review standards are not interchangeable.

## Data Sources And Limits

| Source | Status | Analytical limit |
|---|---|---|
| NOAA IncidentNews | CHEM connector implemented | Selected response-support reporting, not complete incident coverage |
| PHMSA Hazmat export | CHEM importer implemented | Presence flags are not consequence counts |
| National Response Center workbook | CHEM mapping implemented | Current importer does not implement dedicated RN classification |
| WHO Disease Outbreak News | BIO connector implemented | Official notices do not establish cause or intent |
| CDC NNDSS | BIO connector implemented | Provisional aggregate counts may be revised |
| AI misuse fixture | Controlled fixture implemented | No real prompts or model performance claim |
| Fraud fixture | Controlled fixture implemented | No real transaction data or fraud performance claim |

## Governance Decisions

- Alerts retain linked evidence and source limitations.
- Reports require completed analyst review.
- `TL`, `MR`, and `FR` routes remain separate.
- AI misuse, BIO v0.1, and fraud fixture records cannot open CBRN-E doctrine or notification paths.
- CDC provisional revisions are retained rather than silently discarded.
- AI-written reports and hosted deployment remain unapproved.

## What A Later Stage Would Require

An operational release would require the controls documented in
[`deployment-security.md`](deployment-security.md), organizational authorization, named analyst
roles, approved reporting procedures, security testing, and validation against appropriately
labeled source data. EXP and RN work would also require the source-resolution and classification
decisions documented in [`expansion-decision.md`](expansion-decision.md).
