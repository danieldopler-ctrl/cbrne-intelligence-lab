# EXP And RN Expansion Decision

## Decision

Stage 8 documents explosive (`EXP`) and radiological/nuclear (`RN`) source feasibility; it does
not implement new alerts or connectors. This record contains no operational content, material
specifications, sourcing detail, or procedural guidance.

## EXP Context

The ATF U.S. Bomb Data Center publishes annual Explosives Incident Reports as PDF documents.
Those reports provide aggregate public reporting context. The operational Bomb Arson Tracking
System is available to authorized public-safety and law-enforcement users, not as a public
event-level feed for this application.

Decision: an aggregate EXP context display could be produced later from documented public report
tables. Automated event-level EXP review is deferred because a suitable public structured
event-level source has not been selected and validated.

References:

- ATF U.S. Bomb Data Center: https://www.atf.gov/explosives/enforcement-tools-services/us-bomb-data-center
- ATF Explosives Publications: https://www.atf.gov/node/83156

## RN Context

The implemented National Response Center importer handles report workbooks through the current
chemical mapping path. The present code assigns imported NRC report events to `CHEM` or `OTHER`;
it does not classify or score `RAD` or `MULTI` events.

The IAEA Incident and Trafficking Database public resource provides aggregate annual context for
reported incidents involving material outside regulatory control. It is useful as contextual
reference data but is not an event-level source for the alert workflow built here.

Decision: dedicated RN classification could extend the existing NRC mapping with documented
classification rules, then add a separate RN detection adapter. IAEA aggregate data could support
context reporting. Both are deferred until field mapping and evaluation criteria are approved.

References:

- EPA National Response Center overview: https://www.epa.gov/emergency-response/national-response-center
- IAEA Incident and Trafficking Database: https://www.iaea.org/resources/databases/itdb
- IAEA ITDB public dataset resource: https://data.iaea.org/dataset/3ab8e4cb-9b81-4c92-ae1d-238bc0acb8fd/resource/9a935c14-5efe-4f05-bfd2-5328e9aae403

## Rationale

EXP and RN are deferred because current public-source resolution and implemented classification
do not support honest event-level automated claims. The deferral is an evidence-quality decision,
not a conclusion that those risks cannot be assessed in a future authorized build.
