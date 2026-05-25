# Source Manifest

This manifest records proposed official sources and the information that must be captured before operational use. An entry marked `validated for planning` confirms public availability and expected use, not completion of an automated connector.

| Source | Status on 2026-05-24 | Access / format finding | Intended use | Analytical limit |
|---|---|---|---|---|
| NOAA IncidentNews Raw Incident Data | Direct connector implemented | Official public-domain CSV; `commodity` is stored as a normalized column for EPA RMP toxic-substance matching | First live CHEM incident connector and schema validation input | Selected events receiving NOAA OR&R support; not complete and potential release is not actual release or evidence of intent |
| PHMSA Hazmat Incident Reports - Data Mining Tool | Real export imported; Stage 2 deduplication and `LGA` rule implemented | Export uses `Report Number`, `Date Of Incident`, `Commodity Long Name`, `Total Hazmat Fatalities`, `Hazmat Injury Indicator`, `Serious Evacuations`, `Quantity Released`, and `Unit Of Measure`; Yes/No indicators are presence-only and `LGA` is treated as liquid gallons | Incident-level consequence review and liquid-gallon release review | Indicator fields do not provide counts; transportation incident reporting does not establish intent; `GCF` and `SLB` remain unconverted |
| National Response Center (`NRC`) reports | Validated for planning | EPA identifies NRC as the federal reporting point for oil, chemical, radiological, biological and etiological discharges; federal references state reports can be downloaded as Excel files | Release-event import candidate and NCP/NRS reporting context | A record may already reflect reported/handled activity; do not create duplicate-report assumptions |
| WHO Disease Outbreak News (`DON`) API | Validated for planning | Official endpoint `GET /api/news/outbreaks` returns JSON outbreak content | Later BIO event connector | Outbreak reporting does not establish deliberate release |
| CDC NNDSS Weekly Data | Validated for planning | CDC identifies public data catalog access for weekly provisional data from 2014 to present | Later BIO baseline connector | Weekly data is provisional and subject to revision |

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

The first implementation supports CSV, delimited text, and JSON source extracts, a direct NOAA IncidentNews CSV connector, and an importer for official PHMSA Hazmat Incident Report exports. NOAA is selected as the first live machine-readable CHEM incident input because the file structure and public-domain access are documented directly by NOAA. NOAA `commodity` is compared against the EPA RMP regulated toxic substances in `40 CFR 68.130 Table 1` as a review signal. The PHMSA importer is mapped to the observed export headers: numeric fatalities and Yes/No injury and serious-evacuation indicators. A `Yes` value establishes a reported consequence signal for triage; it is not a count.

## Validation Runs

| Date | Source / batch | Records evaluated | Detection result | Limitation retained |
|---|---|---:|---|---|
| 2026-05-24 | NOAA IncidentNews / batch 2 | 4,881 | `CHEM_HAZMAT_V0.2`: 53 maximum-potential-release review alerts and 23 EPA RMP toxic-substance commodity matches | NOAA maximum potential release is not confirmed actual release or intent |
| 2026-05-24 | PHMSA official export / batch 3, pre-Stage 2 baseline | 1,777 rows / 1,752 unique reports | `CHEM_HAZMAT_V0.2`: 269 consequence alerts, 789 EPA RMP toxic-substance commodity matches, and 6 bounded recurrence indicators | Identified 25 repeated rows and 10 duplicate consequence signals; this run is a baseline, not a deduplicated metric |
| 2026-05-25 | PHMSA official export / batch 3, mapping upgraded by controlled `v3` backfill, incident-aware run 5 | 1,777 rows / 1,752 unique reports | `CHEM_HAZMAT_V0.3`: 259 consequence alerts, 783 EPA RMP toxic-substance matches, 2 bounded recurrence indicators, and 8 `LGA` release-quantity alerts | `TL3` count is limited to 7 numeric-fatality alerts; binary injury/serious-evacuation indicators remain `TL2`; prior runs remain audit history |

## Official References

- NOAA IncidentNews: https://incidentnews.noaa.gov/raw/index
- PHMSA: https://www.phmsa.dot.gov/hazmat-program-management-data-and-statistics/data-operations/incident-statistics
- PHMSA DOT catalog record: https://data.transportation.gov/d/rxrf-q3m4
- PHMSA official data dictionary: https://portal.phmsa.dot.gov/HIP_Help/DataDictionary.pdf
- PHMSA regulatory analysis using `LGA` as liquid gallons: https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/news/72641/hm-264-lng-rail-ria-2137-af40.pdf
- EPA RMP regulated substances: https://www.epa.gov/rmp/list-regulated-substances-under-risk-management-program
- 40 CFR 68.130: https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68/section-68.130
- NRC through EPA: https://www.epa.gov/emergency-response/national-response-center
- WHO DON API: https://www.who.int/api/news/outbreaks/sfhelp
- CDC NNDSS: https://www.cdc.gov/nndss/infectious-disease/
