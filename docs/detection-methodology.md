# Detection Methodology

## Method

Detections are deterministic, visible, and tied to source fields. They create review items, not findings of criminal or malicious intent.

Rule set identifier: `CHEM_HAZMAT_V0.4`

| Rule | Trigger | Output | Required interpretation |
|---|---|---|---|
| `CHEM-RELEASE-001` | Normalized `CHEM` event type contains `release` | Low-priority `OBSERVATION`, recommended `TL1` | Logs a source-reported release for review/baselines |
| `CHEM-CONSEQUENCE-001` | Mapped source fields report fatality, injury, or evacuation | `INDICATOR`, score based on consequences, recommended `TL2` or `TL3` | Prioritizes consequence; does not assign intent |
| `CHEM-RECURRENCE-001` | Three or more chemical records in one mapped region and calendar month | `INDICATOR`, recommended `TL2` | A bounded concentration requiring baseline evaluation before it can be called anomalous |
| `CHEM-POTENTIAL-RELEASE-001` | Source reports maximum potential chemical release of at least 10,000 gallons | `INDICATOR`, recommended `TL2` | NOAA potential release is not confirmed actual release and is not toxicity-adjusted |
| `CHEM-SUBSTANCE-001` | Normalized `commodity` matches a regulated toxic substance in `40 CFR 68.130 Table 1` or a documented unambiguous alias | `INDICATOR`, score 40, recommended `TL2` | Flags EPA RMP toxic-substance relevance for review; it does not establish intent, release amount, consequences, or RMP applicability |
| `CHEM-RELEASE-QUANTITY-001` | PHMSA `LGA` quantity or NRC supported liquid-volume quantity reaches at least 10,000 gallons | `INDICATOR`, recommended `TL2` | Excludes unsupported units; a converted quantity is not a hazard or intent determination |
| `CHEM-CONSEQUENCE-COUNT-HIGH-001` | Count-bearing source reports at least 5 injuries | `INDICATOR`, score 75, recommended `TL3` | Active for NRC numeric counts; never inferred from PHMSA Yes/No flags |
| `CHEM-EVACUATION-LARGE-001` | Count-bearing source reports at least 100 evacuees | `INDICATOR`, score 75, recommended `TL3` | Active for NRC numeric counts; source reporting still requires analyst review |
| `CHEM-CORRELATION-001` | NRC and PHMSA reports share an EPA RMP toxic-substance match, state, and three-day window | `CORRELATED_ALERT`, recommended `TL2` | Identifies possible record proximity; does not prove the records describe the same incident |

Routine `CHEM-RELEASE-001` observations are disabled in standard alert runs to avoid converting an entire historical dataset into review workload. An analyst may include them when testing source coverage or building a baseline.

`CHEM-RECURRENCE-001` is not evaluated on NRC annual workbook events in `V0.4`. A first official NRC run showed that a three-record state/month threshold creates routine-volume alerts on a national reporting feed. An NRC recurrence rule requires an expected-volume baseline before it can generate analyst work.

## Consequence Scoring

| Source-reported consequence | Score | Recommended level |
|---|---:|---|
| One or more fatalities | 90 | `TL3` |
| Five or more injuries from a count-bearing source | 75 | `TL3` |
| 100 or more evacuees from a count-bearing source | 75 | `TL3` |
| One or more injuries or evacuees below the above threshold | 50 | `TL2` |

An automated result does not set `TL4`. Immediate danger or mandatory-report conditions require human recognition and emergency action without waiting for platform processing.

PHMSA export fields `Hazmat Injury Indicator` and `Serious Evacuations` are Yes/No presence indicators, not counts. A `Yes` value generates a `TL2` review signal unless numeric fatality information independently warrants `TL3`. The platform does not lower count-based `TL3` thresholds to compensate for missing counts.

NRC annual workbooks provide numeric `NUMBER_INJURED`, `NUMBER_FATALITIES`, and `NUMBER_EVACUATED` fields on the report-level `INCIDENT_DETAILS` sheet. The importer evaluates each count once per `SEQNOS`; it does not sum the counts across the one-to-many material records.

### Potential Release Scoring

| Source-reported maximum potential release | Score | Recommended level |
|---|---:|---|
| 100,000 gallons or more | 70 | `TL2` |
| 10,000 to 99,999 gallons | 45 | `TL2` |

These thresholds identify records for consequence-oriented review. They are not a material hazard calculation and require later calibration against substance, context, and historical baseline.

### Reported Liquid-Gallon Release Scoring

| Source-reported released quantity | Score | Recommended level |
|---|---:|---|
| 100,000 liquid gallons or more for one report | 70 | `TL2` |
| 10,000 to 99,999 liquid gallons for one report | 45 | `TL2` |

PHMSA identifies `LGA` as liquid gallons in official PHMSA analysis materials. Records reported in `GCF` or `SLB` remain preserved for review but are not converted or evaluated by a gallon threshold in this rule version. NRC material rows reported in gallons are evaluated directly. NRC liters, milliliters, quarts, pints, cups, tablespoons, teaspoons, and barrels are converted to gallons with the conversion disclosed in event features; units without a supported liquid-volume conversion remain unscored. NRC `OUNCE(S)` is retained but unscored because the public unit label does not distinguish mass ounces from fluid ounces.

### Regulated Toxic Substance Matching

`CHEM-SUBSTANCE-001` uses the 77 regulated toxic substances in `40 CFR 68.130 Table 1`. The implementation matches normalized exact chemical names and only two unambiguous NOAA text variants at launch: `Chlorine Gas` to `Chlorine`, and `Anhydrous Ammonia` to `Ammonia (anhydrous)`.

The rule does not treat the separate regulated flammable-substance tables as toxic-substance matches. It also does not infer concentration, physical state, regulatory threshold quantity, or threat intent when a source record lacks those facts. Additional aliases require documented analyst review and a version change.

Authority: [40 CFR 68.130](https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68/section-68.130) and [EPA RMP regulated substances](https://www.epa.gov/rmp/list-regulated-substances-under-risk-management-program).

### Incident Deduplication

PHMSA identifies `Report Number` as the unique report identifier and documents that one incident can include multiple lines for multiple shippers, commodities, or packages. Under `CHEM_HAZMAT_V0.4`:

- Consequence alerts are generated once per `Report Number`.
- Recurrence counts use unique report numbers.
- EPA toxic-substance matches are generated once per report and matched regulated substance.
- PHMSA `LGA` quantities are aggregated per report and commodity before threshold evaluation.

NRC annual workbooks use `SEQNOS` as the report identifier. `INCIDENT_COMMONS` and `INCIDENT_DETAILS` each contain one row per report, while `MATERIAL_INVOLVED` can contain multiple rows for a report. NRC consequence counts are taken from the report-level row once; only material names and supported liquid quantities are combined for that report.

### Cross-Source Correlation

`CHEM-CORRELATION-001` links an NRC report and a PHMSA report when both map to the same EPA RMP toxic substance, mapped state codes match, and their reported dates differ by no more than three days. Both source events remain linked to the correlated alert. This is an analyst lead only: chemical, state, and date proximity are not enough to establish a shared incident.

Detection runs are retained as audit history. Results from a baseline run and a corrected run must not be added together as an incident count. Dashboard metrics and the default analyst queue use the latest detection run; historical alerts remain retrievable through the API with `include_history=true`.

## Evaluation Requirements

Before operational credibility claims:

1. Import an approved official historical extract.
2. Select documented significant public events as a benchmark set.
3. Record whether rules produced review-worthy alerts.
4. Record false positives and analyst dispositions.
5. Adjust rules only through a version change with rationale.

The first scoring thresholds are review-prioritization defaults and must be calibrated against real mapped source records.

## Stage 5 Evaluation Workspace

`CHEM_HAZMAT_V0.4` remains unchanged in Stage 5. The evaluation workspace can record selected
official/public CHEM events as reviewed benchmark cases only when an analyst supplies an expected
route, rationale, and citation. An evaluation result then identifies whether the existing versioned
detection run routed those selected records as documented.

These selected-case results are not precision, recall, population detection rates, or proof of
threat intent. Historical detection runs may be compared on the same evaluation set for route and
workload changes; they are never added together as current alert totals.

## Stage 6 Biological Monitoring Rules

Rule set identifier: `BIO_MONITORING_V0.1`

| Rule | Trigger | Output | Required interpretation |
|---|---|---|---|
| `BIO-SURVEILLANCE-ABOVE-PRIOR-MAX-001` | A CDC NNDSS row has usable numeric current-week and prior-52-week-maximum values without disqualifying source flags, and current week is greater than the prior maximum | `INDICATOR`, score 35, recommended `TL1` | Provisional reporting above a source comparison value warrants review; it does not identify cause, deliberate release, or intent |
| `BIO-OFFICIAL-OUTBREAK-REPORT-001` | A WHO Disease Outbreak News record is imported from the official API resource | `OBSERVATION`, score 20, recommended `TL1` | Official public-health report available for context; it is not a threat finding or attribution |

CDC NNDSS rows are imported only through bounded year/week synchronization. A response that reaches
the 10,000-row weekly import cap is rejected rather than processed as an incomplete week. Missing, nonnumeric,
or flagged comparison values remain linked evidence but are excluded from the CDC rule. CDC
weekly data is provisional and subject to later revision and reporting delay. Re-syncing an
identical row creates no new event, while a changed official payload for the same source-row
identity is retained as a linked revision event so later source corrections are not discarded.

WHO DON synchronization uses `GET /api/news/diseaseoutbreaknews`; the similarly named
`/api/news/outbreaks` resource is not the DON source selected after live interface validation.
Automated text interpretation and CDC/WHO correlation are excluded until a documented matching
method can be validated against imported records.

`BIO_MONITORING_V0.1` cannot automatically create `TL3` or `TL4`, notification actions, or
response-doctrine records. Any future escalation capability requires separate evidence,
calibration, and review.

## Stage 7 Source-Cited Reporting

Stage 7 does not add detection rules or scoring thresholds. Reports are built only from alerts
with a recorded analyst review and copy existing rule rationale, evidence fields, citations,
source limitations, and analyst disposition into an exportable record. A single report cannot
mix domain packs or rule-set versions.

Each report displays a fixed domain disclosure so a CHEM indicator is not presented as intent,
a BIO surveillance observation is not presented as deliberate-release attribution, and an AI
misuse fixture review is not presented as real-world safety performance. No AI service or
generated narrative participates in report creation.

### Initial BIO Validation Result

On May 25, 2026, a bounded CDC NNDSS import for MMWR 2026 week 19 returned 8,400 aggregate
rows. Of those, 962 contained usable numeric comparison values without disqualifying source
flags; 7,438 were retained as evidence but excluded from scoring. The CDC rule generated 15
`TL1` review indicators. This volume is manageable for review in the initial local exercise, but
it is not a performance measure or an indication of deliberate activity.

A bounded WHO DON import of the latest 20 official records generated 20 `TL1` official-report
observations. No CDC/WHO correlation rule is implemented in this version because matching
condition, geography, and time fields has not been validated.

After revision-aware CDC handling was added, a repeat sync of MMWR 2026 week 19 classified all
8,400 re-retrieved rows as identical duplicates, produced zero revision records, and a detection
rerun against the canonical imported batch reproduced 15 `TL1` indicators. Automated tests also
cover the changed-payload path and require an official changed row to be retained as a linked
revision rather than discarded as a duplicate.
