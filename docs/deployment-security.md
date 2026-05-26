# Deployment And Security Decision

## Current Decision

The application remains local-only. Danny has not approved hosted deployment. Data is drawn from
approved public sources or controlled synthetic fixtures, and Stage 8 does not transmit reports,
records, or alerts to any outside system.

The development configuration is not approved for operational use: it has no application login,
role controls, TLS termination, rate limiting, production-grade audit protection, or validated
encrypted-at-rest storage.

## Minimum Requirements Before A Hosted Decision

| Control area | Requirement |
|---|---|
| Authentication and access | Individual user accounts, MFA, and roles for analyst, lead, and administrator |
| Data encryption | Encrypted database and raw storage; TLS for web and API traffic |
| Audit integrity | Append-only, tamper-evident audit storage and controlled retention |
| Secret management | Secrets manager for credentials and service tokens; none committed to code |
| Source governance | Approved retention policy, encrypted raw-file storage, and ingest hash verification |
| Network controls | Private database network and protected API ingress |
| Dependency controls | Automated vulnerability checks and approved update process |
| Incident response | Defined process for application compromise or data exposure |
| Analyst identity | Named reviewers; no shared operational analyst accounts |
| Data residency | Recorded storage-jurisdiction decision before accepting operational data |

## Approval Gate

No hosted or operational deployment should proceed without a security review, approved data
handling rules, defined analyst responsibilities, and Danny's explicit authorization.
