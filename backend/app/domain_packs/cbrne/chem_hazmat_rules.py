from app.domain_packs.cbrne.epa_rmp_toxic_substances import (
    ToxicSubstanceMatch,
    match_rmp_toxic_substance,
)


RULE_SET_VERSION = "CHEM_HAZMAT_V0.2"

DEFAULT_RULES = [
    {
        "rule_id": "CHEM-CONSEQUENCE-001",
        "title": "Reported consequence severity",
        "rationale": "Prioritizes source records reporting injury, fatality, or evacuation impacts.",
        "severity": "HIGH",
        "logic_config": {"type": "consequence", "minimum_score": 50},
    },
    {
        "rule_id": "CHEM-RELEASE-001",
        "title": "Chemical or hazardous-material release record",
        "rationale": "Logs a source-reported release for analyst triage and baseline analysis.",
        "severity": "LOW",
        "logic_config": {"type": "release_observation"},
    },
    {
        "rule_id": "CHEM-RECURRENCE-001",
        "title": "Repeated records in common region and month",
        "rationale": "Prioritizes repeated source records sharing a reporting region and calendar month.",
        "severity": "MEDIUM",
        "logic_config": {"type": "regional_recurrence", "minimum_count": 3},
    },
    {
        "rule_id": "CHEM-POTENTIAL-RELEASE-001",
        "title": "Large potential chemical release quantity",
        "rationale": "Prioritizes source-reported maximum potential release quantities for analyst review.",
        "severity": "MEDIUM",
        "logic_config": {"type": "potential_release_quantity", "minimum_gallons": 10000},
    },
    {
        "rule_id": "CHEM-SUBSTANCE-001",
        "title": "EPA RMP toxic substance commodity match",
        "rationale": (
            "Prioritizes source commodities matching a regulated toxic substance in "
            "40 CFR 68.130 Table 1 for analyst review."
        ),
        "severity": "MEDIUM",
        "logic_config": {"type": "epa_rmp_toxic_substance_match", "reference_table": "40 CFR 68.130 Table 1"},
    },
]


def consequence_result(features: dict[str, int]) -> tuple[int, str, str] | None:
    fatalities = features.get("fatalities", 0)
    injuries = features.get("injuries", 0)
    evacuated = features.get("evacuated", 0)
    if fatalities > 0:
        return 90, "HIGH", "TL3"
    if injuries >= 5 or evacuated >= 25:
        return 75, "HIGH", "TL3"
    if injuries > 0 or evacuated > 0:
        return 50, "MEDIUM", "TL2"
    return None


def potential_release_result(features: dict[str, int]) -> tuple[int, str, str] | None:
    gallons = features.get("quantity_released", 0)
    if gallons >= 100000:
        return 70, "MEDIUM", "TL2"
    if gallons >= 10000:
        return 45, "LOW", "TL2"
    return None


def substance_result(commodity: str | None) -> tuple[int, str, str, ToxicSubstanceMatch] | None:
    match = match_rmp_toxic_substance(commodity)
    if match:
        return 40, "MEDIUM", "TL2", match
    return None
