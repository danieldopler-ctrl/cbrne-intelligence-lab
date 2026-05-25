# Detection Methodology

## Method

Stage 1 detections are deterministic, visible, and tied to source fields. They create review items, not findings of criminal or malicious intent.

Rule set identifier: `CHEM_HAZMAT_V0.3`

| Rule | Trigger | Output | Required interpretation |
|---|---|---|---|
| `CHEM-RELEASE-001` | Normalized `CHEM` event type contains `release` | Low-priority `OBSERVATION`, recommended `TL1` | Logs a source-reported release for review/baselines |
| `CHEM-CONSEQUENCE-001` | Mapped source fields report fatality, injury, or evacuation | `INDICATOR`, score based on consequences, recommended `TL2` or `TL3` | Prioritizes consequence; does not assign intent |
| `CHEM-RECURRENCE-001` | Three or more chemical records in one mapped region and calendar month | `INDICATOR`, recommended `TL2` | A bounded concentration requiring baseline evaluation before it can be called anomalous |
| `CHEM-POTENTIAL-RELEASE-001` | Source reports maximum potential chemical release of at least 10,000 gallons | `INDICATOR`, recommended `TL2` | NOAA potential release is not confirmed actual release and is not toxicity-adjusted |
| `CHEM-SUBSTANCE-001` | Normalized `commodity` matches a regulated toxic substance in `40 CFR 68.130 Table 1` or a documented unambiguous alias | `INDICATOR`, score 40, recommended `TL2` | Flags EPA RMP toxic-substance relevance for review; it does not establish intent, release amount, consequences, or RMP applicability |
| `CHEM-RELEASE-QUANTITY-001` | PHMSA reports released quantity in `LGA` and incident/commodity aggregate is at least 10,000 liquid gallons | `INDICATOR`, recommended `TL2` | Applies only to PHMSA standardized liquid gallons; does not convert gas cubic feet or solid pounds |

Routine `CHEM-RELEASE-001` observations are disabled in standard alert runs to avoid converting an entire historical dataset into review workload. An analyst may include them when testing source coverage or building a baseline.

## Consequence Scoring

| Source-reported consequence | Score | Recommended level |
|---|---:|---|
| One or more fatalities | 90 | `TL3` |
| Five or more injuries or 25 or more evacuees | 75 | `TL3` |
| One or more injuries or evacuees below the above threshold | 50 | `TL2` |

An automated result does not set `TL4`. Immediate danger or mandatory-report conditions require human recognition and emergency action without waiting for platform processing.

PHMSA export fields `Hazmat Injury Indicator` and `Serious Evacuations` are Yes/No presence indicators, not counts. A `Yes` value generates a `TL2` review signal unless numeric fatality information independently warrants `TL3`. The platform does not lower count-based `TL3` thresholds to compensate for missing counts.

### Potential Release Scoring

| Source-reported maximum potential release | Score | Recommended level |
|---|---:|---|
| 100,000 gallons or more | 70 | `TL2` |
| 10,000 to 99,999 gallons | 45 | `TL2` |

These thresholds identify records for consequence-oriented review. They are not a material hazard calculation and require later calibration against substance, context, and historical baseline.

### PHMSA Liquid-Gallon Release Scoring

| Source-reported released quantity | Score | Recommended level |
|---|---:|---|
| `LGA` aggregate of 100,000 liquid gallons or more for one report and commodity | 70 | `TL2` |
| `LGA` aggregate of 10,000 to 99,999 liquid gallons for one report and commodity | 45 | `TL2` |

PHMSA identifies `LGA` as liquid gallons in official PHMSA analysis materials. Records reported in `GCF` or `SLB` remain preserved for review but are not converted or evaluated by a gallon threshold in this rule version.

### Regulated Toxic Substance Matching

`CHEM-SUBSTANCE-001` uses the 77 regulated toxic substances in `40 CFR 68.130 Table 1`. The implementation matches normalized exact chemical names and only two unambiguous NOAA text variants at launch: `Chlorine Gas` to `Chlorine`, and `Anhydrous Ammonia` to `Ammonia (anhydrous)`.

The rule does not treat the separate regulated flammable-substance tables as toxic-substance matches. It also does not infer concentration, physical state, regulatory threshold quantity, or threat intent when a source record lacks those facts. Additional aliases require documented analyst review and a version change.

Authority: [40 CFR 68.130](https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68/section-68.130) and [EPA RMP regulated substances](https://www.epa.gov/rmp/list-regulated-substances-under-risk-management-program).

### Incident Deduplication

PHMSA identifies `Report Number` as the unique report identifier and documents that one incident can include multiple lines for multiple shippers, commodities, or packages. Under `CHEM_HAZMAT_V0.3`:

- Consequence alerts are generated once per `Report Number`.
- Recurrence counts use unique report numbers.
- EPA toxic-substance matches are generated once per report and matched regulated substance.
- PHMSA `LGA` quantities are aggregated per report and commodity before threshold evaluation.

Detection runs are retained as audit history. Results from a baseline run and a corrected run must not be added together as an incident count. Dashboard metrics and the default analyst queue use the latest detection run; historical alerts remain retrievable through the API with `include_history=true`.

## Evaluation Requirements

Before operational credibility claims:

1. Import an approved official historical extract.
2. Select documented significant public events as a benchmark set.
3. Record whether rules produced review-worthy alerts.
4. Record false positives and analyst dispositions.
5. Adjust rules only through a version change with rationale.

The first scoring thresholds are review-prioritization defaults and must be calibrated against real mapped source records.
