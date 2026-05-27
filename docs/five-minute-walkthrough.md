# Five-Minute Walkthrough

## Purpose

Use this script for an interview, screen share, or portfolio recording. It explains what the app
does, shows one safe workflow, and avoids unsupported operational claims.

## Setup Before Recording

1. Start PostgreSQL.
2. Start the backend on `http://localhost:8000`.
3. Start the frontend on `http://localhost:3000`.
4. Confirm `http://localhost:8000/health` returns `"status":"ok"`.
5. Refresh the dashboard until metric cards show numbers instead of dashes.

## Opening, 30 Seconds

Say:

> This is CBRN-E Intelligence Lab, a local evidence-linked risk-signal review platform. I built it
> to show how CBRN-E domain judgment, AI misuse review, source governance, and analyst workflow can
> fit together without overstating what automated rules can prove.

Point out:

- The dashboard metrics.
- The warning that automated indicators require analyst review.
- The four main areas: ingest, alerts, evaluations, and reports.

## Section 1: Source And Ingest, 60 Seconds

Click **Sources & Ingest**.

Say:

> The system supports official public sources and controlled fixtures. For chemical incident
> monitoring, it handles NOAA, PHMSA exports, and NRC workbooks. For biological monitoring, it
> handles WHO Disease Outbreak News and CDC NNDSS weekly data. The AI misuse and fraud areas use
> safe synthetic fixtures only.

Point out:

- NOAA public feed sync.
- PHMSA export upload.
- CDC reporting week and WHO report sync.
- Safe AI misuse and fraud evaluation buttons.

Do not click a live connector during a short interview unless the backend is already prepared and
you have time to wait. Use preloaded data when possible.

## Section 2: Alerts, 75 Seconds

Click **Alerts**.

Say:

> Alerts are sorted review items, not conclusions. Each alert is tied to a detection run, a rule
> version, and linked evidence. The default queue shows the latest run so historical calibration
> runs are not added into current totals.

Open one CHEM alert if available.

Point out:

- Rule label and score.
- Recommended review level.
- Evidence block.
- Source limitation.
- Analyst disposition form.

Say:

> The important design choice here is that source limitations travel with the alert. A PHMSA
> presence indicator is not treated as a numeric casualty count. CDC provisional data is treated as
> provisional. Correlation is a lead, not proof that two records are the same incident.

## Section 3: Human Review And Escalation, 60 Seconds

On a CHEM alert detail page, show the analyst review panel.

Say:

> The app keeps automation and human judgment separate. Rules recommend review priority. The
> analyst records disposition, review level, rationale, and any notification assessment. The app
> records a decision; it does not send a message or make an outside report.

Point out:

- `TL0` through `TL4` review levels.
- Response doctrine audit.
- Notification assessment.

If showing BIO, AI misuse, or fraud, say:

> These workflows intentionally block CBRN-E notification and doctrine actions. BIO v0.1 is public
> surveillance review only. AI misuse and fraud are controlled fixtures, not incident records.

## Section 4: Evaluation, 60 Seconds

Click **Evaluations**.

Say:

> The evaluation workspace measures routing behavior against documented expectations. It does not
> claim real-world detection performance unless an approved labeled benchmark set supports that
> claim.

Point out:

- Evaluation sets.
- Detection runs.
- Fixture conformance.
- CHEM reviewed benchmark entry fields.

Say:

> I used this to preserve claim discipline. Fixture routing agreement is not called accuracy.
> Selected public-source benchmarks are not treated as population-level performance.

## Section 5: Reports, 60 Seconds

Click **Reports**.

Say:

> Reports can only be generated from alerts that already have an analyst review. A report cannot mix
> CHEM, BIO, AI misuse, and fraud records, and it cannot mix rule-set versions. It preserves source
> evidence, rule rationale, analyst disposition, and claim limits. It does not call an AI service or
> write new conclusions.

Point out:

- Domain selector.
- Reviewed-alert requirement.
- Claim-limit panel.
- JSON export and printable view, if a report exists.

## Closing, 30 Seconds

Say:

> The project demonstrates how I would approach CBRN-E safety work at an AI lab: evidence first,
> visible rules, documented uncertainty, human review, and strict separation between public
> portfolio material and anything that could increase harmful capability. An operational version
> would require authorized data, access control, security review, and validated evaluation sets.

## Questions To Be Ready For

| Question | Answer |
|---|---|
| Is this operationally deployed? | No. It is a local portfolio build with deployment controls documented separately. |
| Does it detect intent? | No. It prioritizes records for analyst review and preserves evidence. |
| Why synthetic AI misuse cases? | To demonstrate routing without publishing harmful prompts or live model probes. |
| Why is BIO limited to `TL1`? | Public outbreak and surveillance data do not establish cause, deliberate release, or attribution. |
| Why no live AI summaries? | Report generation needs auditability first; AI summaries would need a separate decision and evaluation. |
