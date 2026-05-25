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
