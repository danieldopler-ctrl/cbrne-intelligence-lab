# Portfolio Case Study

## Project

CBRN-E Intelligence Lab is a local analyst workflow application for evidence-linked risk-signal
review. It converts approved public-source records and controlled safe fixtures into auditable
alerts, analyst dispositions, evaluation records, and source-cited reports.

## Why I Built It

The project tests how retired Navy EOD and CBRN-E operational judgment can be translated into an
AI safety and threat-investigation workflow. The goal is not to declare malicious intent from public
data. The goal is to show how an analyst can preserve evidence, apply visible rules, record review
decisions, and keep sensitive domains separated.

## Problem

CBRN-E and AI misuse review both fail when systems overclaim. A public incident record, outbreak
notice, or synthetic safety case may warrant analyst attention, but it does not automatically prove
intent, attribution, causation, or emergency-reporting obligations.

The application addresses this by keeping four controls visible:

- Source evidence and limitations remain attached to every alert.
- Detection rules produce review priorities, not final findings.
- Analyst review is required before reports are generated.
- CHEM, BIO, AI misuse, and fraud review routes remain separate.

## What The System Includes

| Area | Built capability | Purpose |
|---|---|---|
| CHEM incident monitoring | NOAA, PHMSA, and NRC public-source ingestion | Review chemical incident records with evidence and limitations |
| BIO monitoring | WHO Disease Outbreak News and CDC NNDSS synchronization | Track official public-health reports and provisional surveillance indicators |
| AI misuse review | Safe abstract fixture with `MR0` to `MR3` routing | Demonstrate misuse-review workflow without harmful prompt content |
| Fraud portability test | Synthetic fixture with `FR0` to `FR3` routing | Show that the shared workflow can support another risk domain with separate rules |
| Evaluation | Versioned routing and workload comparison | Measure selected-case behavior without claiming broad performance |
| Reporting | Deterministic source-cited reports | Export reviewed evidence and claim limits without AI-written conclusions |

## Design Choices

| Decision | Reason |
|---|---|
| Use official public sources first | Keeps evidence traceable and defensible |
| Keep raw files local and out of git | Prevents accidental publication of source extracts |
| Use deterministic rules | Makes every alert explainable |
| Separate `TL`, `MR`, and `FR` levels | Prevents synthetic safety or fraud records from being treated as CBRN-E incidents |
| Disable BIO notification and doctrine actions | Public surveillance indicators do not establish deliberate release or emergency status |
| Require analyst review before reports | Reports should preserve reviewed evidence, not create unsupported conclusions |
| Defer live AI summaries | AI-written text should not appear until review controls and evaluation are approved |

## Examples Of Review Signals

| Domain | Example review signal | Required interpretation |
|---|---|---|
| CHEM | EPA RMP toxic-substance match | Analyst review item, not proof of intent or regulatory applicability |
| CHEM | NRC count-bearing record with five or more injuries | `TL3` urgent review, source-reported consequence still requires analyst assessment |
| CHEM | NRC and PHMSA record share substance, state, and three-day window | Correlation lead only, not confirmed same incident |
| BIO | CDC current week exceeds prior comparison maximum | `TL1` provisional surveillance review, not attribution |
| BIO | WHO official outbreak report imported | Public-health context, not deliberate-release evidence |
| AI misuse | Abstract case describes safeguard-evasion category | Internal `MR3` review, not a real prompt or model test |
| Fraud | Synthetic record has three abstract risk categories | Internal `FR3` review, not real financial evidence |

## Validation Result

The completed build contains eight committed stages and 15 passing backend tests. The tests cover
source import behavior, deduplication, unit-aware scoring, NRC count handling, CDC revision handling,
AI misuse and fraud fixture routing, notification/doctrine rejection for restricted workflows, and
report-generation gates.

## What This Demonstrates For AI Safety Roles

This project shows the ability to:

- Translate CBRN-E field judgment into explainable review logic.
- Treat source limitations as part of the evidence record.
- Build human-in-the-loop escalation workflows.
- Separate safety review from incident response.
- Avoid harmful public artifacts while still demonstrating technical capability.
- Work with engineers by defining schemas, APIs, tests, controls, and claims limits.

## What It Does Not Claim

The platform does not:

- Confirm malicious intent.
- Identify biological weapons activity.
- Contact external agencies.
- Use classified or restricted data.
- Run live AI model evaluations.
- Prove real-world detection performance.
- Operate as a deployed production system.

## Interview Summary

I built CBRN-E Intelligence Lab to demonstrate how my EOD and CBRN-E background can translate into
AI safety investigation work. The platform ingests official public chemical and biological sources,
applies transparent review rules, links alerts to evidence and limitations, records analyst
dispositions, and generates source-cited reports. I also built a controlled AI misuse assessment
module using safe synthetic cases, because I wanted to demonstrate escalation logic without
publishing harmful prompts or making unsupported safety claims.

The result is a working example of how I approach threat analysis: evidence first, calibrated
claims, human judgment, and strict boundaries around sensitive capability.
