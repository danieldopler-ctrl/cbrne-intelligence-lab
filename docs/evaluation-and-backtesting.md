# Evaluation And Backtesting

## Purpose

Stage 5 adds an evidence-linked measurement workspace for the detection behavior already present
in the platform. Evaluation results are tied to a named evaluation set, a specific detection run,
the rule-set version used for that run, and existing alert evidence.

This stage measures documented routing behavior and review workload. It does not infer malicious
intent or claim complete operational detection performance.

## Evaluation Types

| Type | Input | Interpretable output | Limit |
|---|---|---|---|
| `FIXTURE_CONFORMANCE` | Controlled safe evaluation records, including `AI_MISUSE_SAFE_EVAL_V0.1` and `FRAUD_SAFE_EVAL_V0.1` | Agreement between expected and generated routes | Not real-world model safety, fraud-detection, or threat-detection performance |
| `REVIEWED_BENCHMARK` | Selected public-source CHEM events with analyst citation and expected route | Rule behavior on the labeled records | Not population-level detection rates, intent, or operational readiness |
| Comparison view | Compatible runs for the same evaluation set | Route and workload changes between runs | Does not prove one version is better without adequate labels |

## Records And Evidence

An evaluation set records its type, domain pack, review framework, source basis, and claim limit.
Evaluation cases link to normalized events already stored in the system. A CHEM benchmark case
requires a citation and an analyst rationale; the application does not create a public benchmark
dataset automatically.

An evaluation run links a set to a versioned detection run. Each case result records:

- Expected route (`TL`, `MR`, or `FR`, never mixed within a set).
- Highest generated route.
- Linked alert IDs and rule IDs.
- Whether the route matched, missed expected priority, introduced unexpected high priority,
  differed in another way, or was outside the selected run scope.

Cases outside a selected detection run are recorded as `NOT_EVALUATED` and are excluded from
routing-agreement totals.

## Measures

The report uses these terms:

- `Fixture routing agreement` for controlled fixture route matches.
- `Matched routes` for analyst-labeled benchmark route matches.
- `Missed expected priorities` where a generated route falls below a documented high-priority route.
- `Unexpected high priorities` where a generated route rises above a documented low-priority route.
- Workload counts by linked rule and generated route.
- Reviewed disposition counts where analysts have already recorded outcomes.

The interface does not label fixture agreement as accuracy. Precision, recall, false-positive
rate, and false-negative rate are not shown unless a future approved evaluation design provides
adequate reviewed outcome labels and explicitly documents sampling limits.

## Boundaries

- Existing CHEM detections remain at `CHEM_HAZMAT_V0.4`; this stage does not change thresholds.
- Existing AI misuse detections remain at `AI_MISUSE_V0.1`; the fixture stays abstract and public safe.
- Fraud fixture conformance uses `FRAUD_MONITORING_V0.1`; it contains no real financial records or identifiers.
- Evaluation does not create emergency, doctrine, or external-notification actions.
- No BIO connector, live AI request, or generated narrative is included in Stage 5.

## Public References

- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- NIST AI 600-1, Generative Artificial Intelligence Profile: https://doi.org/10.6028/NIST.AI.600-1
- Anthropic Responsible Scaling Policy: https://www.anthropic.com/responsible-scaling-policy
