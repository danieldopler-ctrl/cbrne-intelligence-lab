# Safety And Data Governance

## Purpose

The platform supports defensive analysis of approved source records. It must not generate instructions, sourcing guidance, dispersal guidance, or procedural information that increases harmful CBRN-E capability.

## Data Classes

| Class | Handling |
|---|---|
| Public official source | May be locally ingested subject to source terms and documented limitations |
| User-provided approved source | Local only unless publication is separately approved |
| Restricted source | Do not ingest without authorization and appropriate security controls |
| Test fixture | Minimal, clearly labeled, non-sensitive record used for automated testing |

## Required Controls

- Raw source snapshots remain local and are gitignored.
- Each ingest stores provenance and a cryptographic hash.
- Alerts display source limitations and evidence.
- External reporting decisions are made by authorized humans.
- AI summaries are deferred until evidence and review workflow can be audited.
- Public repository review is required before publishing any data or outputs.
- AI misuse fixture descriptions must be safe for unrestricted public reading and remain at the behavioral-category level.
- AI misuse fixture alerts are restricted to internal safety review and cannot create notification or incident-doctrine actions.
- BIO monitoring uses public aggregate or official report data only; its v0.1 observation indicators cannot create notification or incident-doctrine actions.
- Reports can be generated only from analyst-reviewed alerts and cannot combine records from separate domain packs.
- Report export reproduces stored evidence, citations, limitations, and review records without AI-written text or automated delivery.
- Fraud portability testing uses synthetic abstract cases only and cannot create notification or CBRN-E doctrine actions.

## Prohibited System Outputs

- Instructions for developing, producing, acquiring, or deploying CBRN-E agents or devices.
- Automatic attribution of criminal or hostile intent from public records.
- Automatic agency notification or claimed response-plan activation.
- Unreviewed public identification of an individual, organization, or facility as a threat.
- Harmful prompt corpora, live-model jailbreak requests, or operationally specific AI misuse examples.

## AI Misuse Fixture Control

The AI Misuse Risk Assessment Module uses synthetic abstract records only. It evaluates rule and
workflow behavior, not a model's response to a harmful request. Case summaries omit named
hazardous materials, quantities, acquisition pathways, delivery methods, and evasion
instructions. Output levels are `MR0` to `MR3` internal review routes and are never interpreted as
incident `TL` levels.

## Biological Monitoring Control

`BIO_MONITORING_V0.1` uses bounded synchronization of WHO Disease Outbreak News records and CDC
NNDSS weekly aggregate provisional reports. CDC source flags and missing comparison values are
retained rather than converted into detections. Automated BIO output is limited to `TL1`
analyst-review indicators in this version and cannot be used as a finding of cause, deliberate
release, intent, attribution, or emergency-plan applicability.

## Report Export Control

Source-cited reports are review records, not new findings. The reporting service requires an
analyst review for every included alert, enforces one domain pack and rule-set version per
report, and displays a domain-specific disclosure before export. JSON download and printable
HTML are local analyst actions. Stage 7 does not send reports externally or call an AI service.

## Fraud Fixture Control

`FRAUD_MONITORING_V0.1` is a controlled architecture test, not a fraud-monitoring product. Its
fixture contains abstract category flags and summaries only, with no personal identifiers,
financial identifiers, real transactions, or referral instructions. `FRAUD_REVIEW` uses `FR0`
through `FR3` and remains isolated from CBRN-E incident escalation. Any future use with real
financial records requires separate privacy, authorization, security, and evaluation decisions.
