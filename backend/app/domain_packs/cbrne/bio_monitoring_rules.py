RULE_SET_VERSION = "BIO_MONITORING_V0.1"

DEFAULT_RULES = [
    {
        "rule_id": "BIO-SURVEILLANCE-ABOVE-PRIOR-MAX-001",
        "title": "Reported weekly count above prior 52-week maximum",
        "rationale": (
            "Prioritizes a CDC NNDSS weekly provisional report when its numeric current-week "
            "count is above the source-provided prior 52-week maximum."
        ),
        "severity": "LOW",
        "logic_config": {
            "type": "source_reported_prior_max_comparison",
            "source": "CDC_NNDSS",
            "maximum_automated_level": "TL1",
        },
    },
    {
        "rule_id": "BIO-OFFICIAL-OUTBREAK-REPORT-001",
        "title": "Official WHO outbreak report available",
        "rationale": "Logs an official WHO Disease Outbreak News record for analyst context.",
        "severity": "LOW",
        "logic_config": {
            "type": "official_outbreak_report_observation",
            "source": "WHO_DON",
            "maximum_automated_level": "TL1",
        },
    },
]


def cdc_above_prior_max(features: dict[str, object]) -> tuple[int, str, str] | None:
    if features.get("source_system") != "CDC_NNDSS" or not features.get("scorable"):
        return None
    current_week = features.get("current_week_count")
    prior_max = features.get("previous_52_week_max")
    if not isinstance(current_week, (int, float)) or not isinstance(prior_max, (int, float)):
        return None
    if current_week > prior_max:
        return 35, "LOW", "TL1"
    return None
