# Response Doctrine Mapping

The platform identifies potentially applicable doctrine for reviewed alerts. It cannot activate a plan, designate command, or direct responders.

| Doctrine | Alert context | Required recording behavior |
|---|---|---|
| `NIMS` / `ICS` | Active incident requiring coordinated response | Capture incident command, unified command, or EOC reference only if provided or verified |
| `NRF` | Possible broader government coordination | Mark as potentially applicable unless verified activation is documented |
| `ESF #8` | BIO, toxic exposure, casualty, or medical-surge consequence | Flag public-health/medical coordination review |
| `ESF #10` | Oil or hazardous-material release | Flag hazardous-material coordination review |
| `NCP` / `NRS` | Reportable environmental discharge | Pair with NRC reporting assessment |
| `BIA` | Significant biological incident context | Capture biological-response planning relevance |
| `NRIA` | Nuclear/radiological incident context | Capture nuclear/radiological-response planning relevance |
| `NARP` | Nuclear weapon accident/incident context only | Do not apply to general radiological events |
| National Prevention Framework | Credible terrorism-related prevention context | Capture authorized information-sharing review |

## UI Requirement

The alert review interface must distinguish:

- `POTENTIALLY_APPLICABLE`: analyst identifies doctrine worth considering.
- `APPLICABLE_VERIFIED`: official activation/applicability is supported by a recorded reference.
- `NOT_APPLICABLE`: reviewer determines it does not apply.

## References

- FEMA NIMS: https://www.fema.gov/emergency-managers/nims
- FEMA NRF: https://www.fema.gov/emergency-managers/national-preparedness/frameworks/response
- FEMA FIOPs and incident annexes: https://www.fema.gov/emergency-managers/national-preparedness/frameworks/federal-interagency-operational-plans
- EPA National Response System: https://www.epa.gov/emergency-response/national-response-system
- DoD NARP resource: https://www.acq.osd.mil/ncbdp/narp/
