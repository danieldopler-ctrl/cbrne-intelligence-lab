from app.domain_packs.cbrne.epa_rmp_toxic_substances import (
    ToxicSubstanceMatch,
    match_rmp_toxic_substance,
)


RULE_SET_VERSION = "CHEM_HAZMAT_V0.4"

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
    {
        "rule_id": "CHEM-RELEASE-QUANTITY-001",
        "title": "Large reported liquid-gallon release quantity",
        "rationale": (
            "Prioritizes source-reported liquid quantities expressed in or converted to "
            "gallons; unsupported units are excluded."
        ),
        "severity": "MEDIUM",
        "logic_config": {"type": "reported_liquid_release_quantity", "minimum_gallons": 10000},
    },
    {
        "rule_id": "CHEM-CONSEQUENCE-COUNT-HIGH-001",
        "title": "High reported injury count",
        "rationale": "Prioritizes count-bearing source reports with five or more reported injuries.",
        "severity": "HIGH",
        "logic_config": {"type": "reported_count_consequence", "minimum_injuries": 5},
    },
    {
        "rule_id": "CHEM-CONSEQUENCE-COUNT-MODERATE-001",
        "title": "Reported consequence count",
        "rationale": "Prioritizes count-bearing source reports with lower injury or evacuation counts.",
        "severity": "MEDIUM",
        "logic_config": {
            "type": "reported_count_consequence",
            "minimum_injuries": 1,
            "minimum_evacuations": 1,
        },
    },
    {
        "rule_id": "CHEM-EVACUATION-LARGE-001",
        "title": "Large reported evacuation count",
        "rationale": "Prioritizes count-bearing source reports with 100 or more reported evacuations.",
        "severity": "HIGH",
        "logic_config": {"type": "reported_count_consequence", "minimum_evacuations": 100},
    },
    {
        "rule_id": "CHEM-CORRELATION-001",
        "title": "Cross-source chemical incident proximity",
        "rationale": (
            "Prioritizes NRC and PHMSA reports sharing an EPA RMP toxic substance, state, "
            "and three-day window."
        ),
        "severity": "MEDIUM",
        "logic_config": {
            "type": "cross_source_proximity",
            "sources": ["NRC", "PHMSA"],
            "days": 3,
            "commodity_basis": "shared_epa_rmp_toxic_substance",
        },
    },
]


def consequence_result(features: dict[str, object]) -> tuple[int, str, str] | None:
    fatalities = int(features.get("fatalities", 0) or 0)
    injuries = int(features.get("injuries", 0) or 0)
    evacuated = int(features.get("evacuated", 0) or 0)
    if fatalities > 0:
        return 90, "HIGH", "TL3"
    if features.get("consequence_basis") == "binary_indicators_with_numeric_fatalities":
        if injuries > 0 or evacuated > 0:
            return 50, "MEDIUM", "TL2"
        return None
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


def reported_liquid_release_result(gallons: float) -> tuple[int, str, str] | None:
    if gallons >= 100000:
        return 70, "MEDIUM", "TL2"
    if gallons >= 10000:
        return 45, "LOW", "TL2"
    return None


def count_consequence_results(features: dict[str, object]) -> list[tuple[str, int, str, str]]:
    if features.get("source_capability") != "count_bearing":
        return []
    injuries = int(features.get("injuries_count", 0) or 0)
    evacuated = int(features.get("evacuations_count", 0) or 0)
    results: list[tuple[str, int, str, str]] = []
    if injuries >= 5:
        results.append(("CHEM-CONSEQUENCE-COUNT-HIGH-001", 75, "HIGH", "TL3"))
    elif injuries > 0:
        results.append(("CHEM-CONSEQUENCE-COUNT-MODERATE-001", 50, "MEDIUM", "TL2"))
    if evacuated >= 100:
        results.append(("CHEM-EVACUATION-LARGE-001", 75, "HIGH", "TL3"))
    elif evacuated > 0 and injuries == 0:
        results.append(("CHEM-CONSEQUENCE-COUNT-MODERATE-001", 50, "MEDIUM", "TL2"))
    return results


def substance_result(commodity: str | None) -> tuple[int, str, str, ToxicSubstanceMatch] | None:
    match = match_rmp_toxic_substance(commodity)
    if match:
        return 40, "MEDIUM", "TL2", match
    return None
