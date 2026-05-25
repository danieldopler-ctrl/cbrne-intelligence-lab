# AI Misuse Risk Assessment Module

## Purpose

The `AI_MISUSE_V0.1` domain pack tests an internal safety-review workflow using controlled,
abstract records. It is designed to demonstrate traceable safeguard assessment without storing
harmful prompts, probing a live model, or creating operational hazardous-content examples.

## Evaluation Set

`AI_MISUSE_SAFE_EVAL_V0.1` contains 34 synthetic test cases. Every case is safe for publication:
it describes a behavioral category at a high level and contains no named hazardous materials,
amounts, acquisition paths, delivery methods, or evasion instructions.

| Case class | Count | Intended route |
|---|---:|---|
| Allowed educational or safety context | 8 | `MR0` |
| Ambiguous sensitive-domain request | 8 | `MR1` |
| Described restricted-assistance request | 8 | `MR2` |
| Described safeguard-evasion or concealment request | 6 | `MR3` |
| Compound high-risk signal | 4 | `MR3` |

This set validates rule routing and analyst workflow behavior. It is not training data, real user
data, a prompt library, or evidence about model capability.

## Review Levels

| Level | Meaning | Handling |
|---|---|---|
| `MR0` | Allowed or log-only fixture case | Retained for evaluation; no alert by default |
| `MR1` | Ambiguous case | Analyst review item |
| `MR2` | Restricted-assistance signal | High-priority internal safety review |
| `MR3` | Safeguard-evasion or compound-risk signal | Urgent internal safety review |

`MR` levels are separate from incident `TL` levels. The API rejects notification and
response-doctrine records for AI misuse fixture alerts. The module cannot initiate agency contact,
emergency action, or public attribution.

## Rule Set

| Rule | Signal |
|---|---|
| `AIM-DUAL-USE-REVIEW-001` | Ambiguous sensitive-domain context |
| `AIM-CAPABILITY-UPLIFT-001` | Described restricted-assistance or harmful optimization category |
| `AIM-SAFEGUARD-EVASION-001` | Described safeguard-bypass attempt |
| `AIM-CONCEALMENT-001` | Described oversight-avoidance attempt |
| `AIM-TOOL-ENABLEMENT-001` | High-risk signal combined with delegated tool action |
| `AIM-COMPOUND-RISK-001` | Multiple high-risk signals in one abstract case |

## Evaluation Claim

The evaluation endpoint reports fixture conformance: expected route compared with generated route,
missed high-priority cases, unexpected escalations, and rule trigger counts. Results must not be
described as real-world model performance, red-team success, or a safety guarantee.

## Local Validation

On 2026-05-25, the controlled fixture was imported into the local PostgreSQL application and
evaluated under `AI_MISUSE_V0.1`:

| Measure | Result |
|---|---:|
| Safe abstract cases evaluated | 34 |
| Cases expected to create a review alert | 26 |
| Rule-supported alerts generated | 35 |
| Cases with expected highest `MR` route | 34 / 34 |
| Missed `MR2` or `MR3` routes | 0 |
| Unexpected escalations | 0 |

Several cases correctly trigger more than one rule, so alert count is greater than alerted-case
count. These are fixture-conformance results only.

## Public References

- NIST AI 600-1, Generative Artificial Intelligence Profile: https://doi.org/10.6028/NIST.AI.600-1
- Anthropic Responsible Scaling Policy: https://www.anthropic.com/responsible-scaling-policy
- MITRE ATLAS: https://atlas.mitre.org/
