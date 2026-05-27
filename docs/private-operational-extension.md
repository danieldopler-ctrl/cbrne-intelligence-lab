# Private Operational Extension

## Purpose

This document describes a possible private extension for restricted or sensitive-by-aggregation
research material. It is an interview-safe design record, not an implemented module and not a
source of operational hazardous-content guidance.

## Decision

Do not add restricted or sensitive-by-aggregation CBRN-E research material to the public GitHub
repository. Do not process it through hosted tools or shared chats without an approved handling
decision. The current public application remains limited to official public sources and controlled
safe fixtures.

## Why A Separate Private System Is Required

Open-source technical material can become more sensitive when compiled into:

- Precursor groupings.
- Process-stage indicators.
- End-product inference aids.
- Acquisition or query-chain patterns.
- Hazardous process points.
- Evasion or concealment indicators.

Those compiled relationships may be useful for authorized defensive analysis, but they should not
be exposed in a public portfolio app.

## Intended Private Use Case

An authorized private extension could review query logs or approved internal records and ask:

- Does activity match a controlled indicator category?
- Is the activity isolated, repeated, clustered, or escalating?
- What benign explanations should be considered?
- Which review route should an authorized analyst use?
- What evidence, citation, and limitation should remain attached to the record?

The system should classify review priority and preserve evidence. It should not display production
pathways, procedural detail, or hazardous outcome instructions.

## Data Handling Boundary

| Allowed in private prototype | Excluded from public app |
|---|---|
| Redacted indicator categories | Precursor-to-agent recipes |
| Source citations and handling labels | Synthesis steps, quantities, conditions, or optimization |
| Hazard class and review rationale | Acquisition pathways or process-control instructions |
| Legitimate-use context | Evasion guidance |
| Analyst disposition and audit logs | Biological design or capability-increasing guidance |
| Synthetic demonstration records | Real query logs without authorization |

## Recommended Architecture

| Component | Requirement |
|---|---|
| Storage | Encrypted local storage or approved secure environment |
| Repository | Separate private repo with no public remote by default |
| Authentication | Named users, MFA, and role-based permissions before shared use |
| Audit | Log record access, changes, exports, and review decisions |
| Exports | Disabled by default; approved redacted export only |
| Model use | Local model first; no telemetry or prompt logging to external services |
| Logs | Query logs stored only with authorization and retention rules |
| Backups | Encrypted backup media stored separately |
| Review | Human approval before adding source classes, rules, or outputs |

## Local Model Requirements

A local LLM workflow should be treated as part of the controlled system:

- Model runtime must not upload prompts, files, logs, or telemetry.
- Inputs and outputs stay inside the encrypted workspace.
- Temporary files, caches, and extracted text are included in the protection plan.
- The model receives only the minimum record fields needed for classification.
- Outputs are constrained to review category, rationale, confidence, and allowed references.
- The model must refuse or redact procedural hazardous detail.

## Candidate Review Levels

| Level | Meaning | Handling |
|---|---|---|
| `IR0` | Benign or administrative match | Retain only if needed for audit |
| `IR1` | Weak or ambiguous indicator | Analyst review |
| `IR2` | Repeated or multi-category pattern | Senior analyst review |
| `IR3` | High-priority controlled-indicator cluster | Internal escalation assessment |
| `IR4` | Immediate danger or mandatory-report facts independently verified | Do not delay emergency or required reporting |

`IR` means interest review. It should not be treated as proof of intent, threat, or illegal conduct.

## Escalation Design

| Review level | Internal route | External posture |
|---|---|---|
| `IR0` | Log or dismiss | None |
| `IR1` | Analyst review | None based solely on automation |
| `IR2` | Lead review | Assess whether additional authorized information is needed |
| `IR3` | Security, legal, or authorized reporting lead review | External referral assessment only with approved authority |
| `IR4` | Emergency leadership and authorized response process | Do not delay emergency action or mandatory reporting |

The application should record assessment decisions. It should not automatically send reports,
emails, tips, or agency notifications.

## Interview-Safe Explanation

Use this wording:

> I intentionally kept the public artifact limited to official incident and surveillance data plus
> safe synthetic fixtures. A private operational extension could support authorized review of
> sensitive-by-aggregation research indicators or query logs, but it would require encrypted
> storage, access controls, audit logging, redacted displays, and clear limits on what the system is
> allowed to output. I would not put precursor chains or procedural hazardous detail in a public
> demo.

## Build Gate

Before implementation, define:

1. Source markings and ownership.
2. Authorization to digitize and restructure the material.
3. Allowed fields and excluded details.
4. Encryption, access, audit, and backup controls.
5. Export and screenshot policy.
6. Whether a local model runtime is approved.
7. Synthetic test data for the first build.
8. Human review process for any real query logs.

No restricted dataset should be loaded until this gate is complete.
