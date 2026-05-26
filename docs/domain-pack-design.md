# Domain Pack Design

## Reusable Core

The platform core handles source registration, import history, normalized events, detection execution, alerts, reviews, notifications, doctrine mapping, evaluation, and audit history.

## CBRN-E Pack

The first pack adds:

- Hazard domain values and source mapping.
- CHEM/hazmat consequence and recurrence rules.
- CBRN-E escalation doctrine and reporting-path references.
- Later BIO, EXP, and RN source and rule sets.

## Fraud Extension Path

`FRAUD_MONITORING_V0.1` now tests portability on synthetic, abstract fixture records. It reuses
common storage, evidence, alert, review, evaluation, report, and audit records while adding
fraud-specific rules and `FRAUD_REVIEW` routing. It cannot open CBRN-E notification or doctrine
workflows.

An operational fraud domain pack would still need:

- Transactions, accounts, devices, merchants, claims, or chargeback entities.
- Fraud-specific detection rules and outcome labels.
- Personally identifiable and financial data protections.
- A separate escalation and external-referral framework based on the operating entity's obligations.

Machine-learning training is deferred until lawful, representative, labeled outcomes exist and can be measured against transparent rule performance.

## AI Misuse Risk Assessment Pack

`AI_MISUSE_V0.1` reuses source provenance, normalized records, rules, alerts, reviews, evaluation,
and audit history. It uses separate internal review levels (`MR0` through `MR3`) because a
synthetic assessment-case signal is not a real-world incident or a mandatory-report condition.

Initial input is a public-safe abstract fixture set only. The pack does not accept free-form
prompts, call an AI provider, store model completions, or open response-doctrine or external
notification workflows.
