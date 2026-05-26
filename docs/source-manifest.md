# Source Manifest

This manifest records proposed official sources and the information that must be captured before operational use. An entry marked `validated for planning` confirms public availability and expected use, not completion of an automated connector.

| Source | Status on 2026-05-24 | Access / format finding | Intended use | Analytical limit |
|---|---|---|---|---|
| NOAA IncidentNews Raw Incident Data | Direct connector implemented | Official public-domain CSV; `commodity` is stored as a normalized column for EPA RMP toxic-substance matching | First live CHEM incident connector and schema validation input | Selected events receiving NOAA OR&R support; not complete and potential release is not actual release or evidence of intent |
| PHMSA Hazmat Incident Reports - Data Mining Tool | Real export imported; Stage 2 deduplication and `LGA` rule implemented | Export uses `Report Number`, `Date Of Incident`, `Commodity Long Name`, `Total Hazmat Fatalities`, `Hazmat Injury Indicator`, `Serious Evacuations`, `Quantity Released`, and `Unit Of Measure`; Yes/No indicators are presence-only and `LGA` is treated as liquid gallons | Incident-level consequence review and liquid-gallon release review | Indicator fields do not provide counts; transportation incident reporting does not establish intent; `GCF` and `SLB` remain unconverted |
| National Response Center (`NRC`) annual reports | Official 2024 workbook imported and detection run validated locally | Official XLSX is relational: `INCIDENT_COMMONS` and `INCIDENT_DETAILS` contain one row per `SEQNOS`; `MATERIAL_INVOLVED` contains one-to-many material rows | Numeric consequence review, reported-release monitoring, and chemically bounded NRC/PHMSA correlation | NRC identifies the workbook as initial, unvalidated data that may be incomplete, inaccurate, or revised; proximity is not incident identity or intent |
| WHO Disease Outbreak News (`DON`) API | Connector in local development | Official `GET /api/news/diseaseoutbreaknews` resource returned DON records on 2026-05-25 with metadata including `DonId`, `Title`, `PublicationDateAndTime`, `ItemDefaultUrl`, `Summary`, and `Provider`; `/api/news/outbreaks` is not used for DON ingestion | Official BIO report observation and source evidence | Selected public reports are not exhaustive and do not establish deliberate release, intent, or attribution |
| CDC NNDSS Weekly Data | Connector in local development | Official Socrata dataset `x9gk-5huc` was live and updated 2026-05-20; documented fields include reporting area, MMWR year/week, condition label, `m1` through `m4`, and associated flags | Weekly provisional BIO surveillance review indicator | Counts are provisional, subject to revision and reporting delay; deviation does not establish cause or intent |

## Source Registration Requirements

Before a dataset is loaded, capture:

- Official dataset title and publishing organization.
- Source URL and retrieval timestamp.
- File format or endpoint used.
- Access terms and allowed use.
- Local raw snapshot SHA-256 hash.
- Fields mapped into normalized events.
- Any suppressed or sensitive fields.
- Source limitations that must appear in alerts.

## Stage 1 Selection

The implementation supports CSV, delimited text, and JSON source extracts, a direct NOAA IncidentNews CSV connector, an importer for official PHMSA Hazmat Incident Report exports, and an importer for NRC annual XLSX workbooks. NOAA `commodity` is compared against the EPA RMP regulated toxic substances in `40 CFR 68.130 Table 1` as a review signal. The PHMSA importer is mapped to numeric fatalities and Yes/No injury and serious-evacuation indicators; a `Yes` value establishes a triage signal, not a count. The NRC importer joins official sheets by `SEQNOS`, retains one normalized event per report, and evaluates numeric consequence counts only once per report.

## Stage 6 BIO Source Mapping

The CDC connector requests a bounded MMWR year/week slice, capped at 10,000 rows and rejected if
that cap is reached rather than processing a partial reporting week, from
`https://data.cdc.gov/resource/x9gk-5huc.json` and maps public aggregate rows into `BIO`
events. It retains `states`, `year`, `week`, `label`, `m1`, `m1_flag`, `m2`, `m2_flag`,
`m3`, `m3_flag`, `m4`, `m4_flag`, `location1`, `location2`, and `sort_order`. Rows with
missing numeric `m1`/`m2` values or source flags on those values remain evidence records but do
not create prior-maximum indicators. Repeated rows with identical official payloads are counted
as duplicates; if a provisional row is later returned with changed official values, the changed
payload is retained as a revision event linked to the stable source-row identity.

The WHO connector requests a bounded latest-record selection from
`https://www.who.int/api/news/diseaseoutbreaknews` and maps observed official metadata only.
The similar `/api/news/outbreaks` resource returned an empty collection during validation and is
not used as the DON connector target.

## Validation Runs

| Date | Source / batch | Records evaluated | Detection result | Limitation retained |
|---|---|---:|---|---|
| 2026-05-24 | NOAA IncidentNews / batch 2 | 4,881 | `CHEM_HAZMAT_V0.2`: 53 maximum-potential-release review alerts and 23 EPA RMP toxic-substance commodity matches | NOAA maximum potential release is not confirmed actual release or intent |
| 2026-05-24 | PHMSA official export / batch 3, pre-Stage 2 baseline | 1,777 rows / 1,752 unique reports | `CHEM_HAZMAT_V0.2`: 269 consequence alerts, 789 EPA RMP toxic-substance commodity matches, and 6 bounded recurrence indicators | Identified 25 repeated rows and 10 duplicate consequence signals; this run is a baseline, not a deduplicated metric |
| 2026-05-25 | PHMSA official export / batch 3, mapping upgraded by controlled `v3` backfill, incident-aware run 5 | 1,777 rows / 1,752 unique reports | `CHEM_HAZMAT_V0.3`: 259 consequence alerts, 783 EPA RMP toxic-substance matches, 2 bounded recurrence indicators, and 8 `LGA` release-quantity alerts | `TL3` count is limited to 7 numeric-fatality alerts; binary injury/serious-evacuation indicators remain `TL2`; prior runs remain audit history |
| 2026-05-25 | NRC official 2024 workbook / batch 4, initial run 6 | 22,966 reports / 20,323 material-linked CHEM events | Identified 2,404 state/month recurrence alerts on an uncalibrated national feed | Run retained as audit history; NRC recurrence scoring was excluded pending a baseline model |
| 2026-05-25 | NRC official 2024 workbook / batch 5, final corrected mapping run 8 | 22,966 reports / 20,323 material-linked CHEM events | `CHEM_HAZMAT_V0.4`: 358 EPA RMP matches, 45 high injury-count alerts, 43 large-evacuation alerts, 119 liquid-gallon quantity alerts, 809 moderate consequence-count alerts, and 119 fatality consequence alerts | 1,493 current alerts total; 207 `TL3`; ambiguous NRC `OUNCE(S)` is retained but not converted; zero chemical-specific NRC/PHMSA correlations observed in this local run; correlation behavior is covered by test data |
| 2026-05-25 | WHO Disease Outbreak News official API / batch 8, bounded latest-20 import, run 11 | 20 official reports | `BIO_MONITORING_V0.1`: 20 `BIO-OFFICIAL-OUTBREAK-REPORT-001` observations, all recommended `TL1` | Official public-health report context only; does not establish deliberate release, intent, attribution, or emergency status |
| 2026-05-25 | CDC NNDSS official API / initial batch 9, revision-aware repeat sync batch 11, validation run 14; MMWR 2026 week 19 | Initial import: 8,400 weekly rows; 962 numeric/scorable; 7,438 retained and excluded from scoring. Repeat sync: 8,400 identical duplicates, 0 revisions, 0 new events. | `BIO_MONITORING_V0.1`: 15 `BIO-SURVEILLANCE-ABOVE-PRIOR-MAX-001` indicators, all recommended `TL1`, reproduced from the canonical imported batch | Counts are provisional and subject to revision/delay; changed official rows are retained as linked revisions; a prior-max exceedance is an analyst-review item only |

## Official References

- NOAA IncidentNews: https://incidentnews.noaa.gov/raw/index
- PHMSA: https://www.phmsa.dot.gov/hazmat-program-management-data-and-statistics/data-operations/incident-statistics
- PHMSA DOT catalog record: https://data.transportation.gov/d/rxrf-q3m4
- PHMSA official data dictionary: https://portal.phmsa.dot.gov/HIP_Help/DataDictionary.pdf
- PHMSA regulatory analysis using `LGA` as liquid gallons: https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/news/72641/hm-264-lng-rail-ria-2137-af40.pdf
- EPA RMP regulated substances: https://www.epa.gov/rmp/list-regulated-substances-under-risk-management-program
- 40 CFR 68.130: https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68/section-68.130
- NRC through EPA: https://www.epa.gov/emergency-response/national-response-center
- NRC public incident data and data dictionary: https://nrc.uscg.mil/
- NRC 2024 annual workbook: https://nrc.uscg.mil/FOIAFiles/CY24.xlsx
- NRC data dictionary workbook: https://nrc.uscg.mil/FOIAFiles/DataDictionary.xlsx
- WHO DON API: https://www.who.int/api/news/diseaseoutbreaknews/sfhelp
- WHO DON live resource: https://www.who.int/api/news/diseaseoutbreaknews
- CDC NNDSS Weekly Data API resource: https://data.cdc.gov/resource/x9gk-5huc.json
- CDC NNDSS: https://www.cdc.gov/nndss/infectious-disease/
