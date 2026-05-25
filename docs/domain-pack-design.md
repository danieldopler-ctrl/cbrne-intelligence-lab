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

A fraud domain pack can use the same core workflow, but it needs:

- Transactions, accounts, devices, merchants, claims, or chargeback entities.
- Fraud-specific detection rules and outcome labels.
- Personally identifiable and financial data protections.
- A separate escalation and external-referral framework based on the operating entity's obligations.

Machine-learning training is deferred until lawful, representative, labeled outcomes exist and can be measured against transparent rule performance.
