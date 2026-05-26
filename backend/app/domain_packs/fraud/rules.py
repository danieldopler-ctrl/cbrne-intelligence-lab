RULE_SET_VERSION = "FRAUD_MONITORING_V0.1"

DEFAULT_RULES = [
    {
        "rule_id": "FRD-VELOCITY-INDICATOR-001",
        "title": "Elevated activity pattern",
        "rationale": "Routes an abstract elevated-activity fixture category for fraud analyst review.",
        "severity": "LOW",
        "logic_config": {"review_level": "FR1", "feature": "velocity_indicator"},
    },
    {
        "rule_id": "FRD-DUPLICATE-INDICATOR-001",
        "title": "Duplicate-submission pattern",
        "rationale": "Routes an abstract duplicate-submission fixture category for fraud analyst review.",
        "severity": "LOW",
        "logic_config": {"review_level": "FR1", "feature": "duplicate_indicator"},
    },
    {
        "rule_id": "FRD-AMOUNT-INDICATOR-001",
        "title": "Amount-outlier pattern",
        "rationale": "Routes an abstract amount-outlier fixture category for fraud analyst review.",
        "severity": "LOW",
        "logic_config": {"review_level": "FR1", "feature": "amount_outlier_indicator"},
    },
    {
        "rule_id": "FRD-IDENTITY-INDICATOR-001",
        "title": "Identity-consistency pattern",
        "rationale": "Routes an abstract identity-consistency fixture category for fraud analyst review.",
        "severity": "LOW",
        "logic_config": {"review_level": "FR1", "feature": "identity_consistency_indicator"},
    },
    {
        "rule_id": "FRD-COMPOUND-INDICATOR-001",
        "title": "Combined fraud-review pattern",
        "rationale": "Routes a synthetic case with multiple abstract indicators for analyst investigation.",
        "severity": "MEDIUM",
        "logic_config": {"review_level": "FR2", "minimum_signals": 2},
    },
    {
        "rule_id": "FRD-HIGH-PRIORITY-INDICATOR-001",
        "title": "High-priority combined pattern",
        "rationale": "Routes a synthetic case with several abstract indicators for urgent analyst review.",
        "severity": "HIGH",
        "logic_config": {"review_level": "FR3", "minimum_signals": 3},
    },
]

SIGNAL_RULES = {
    "velocity_indicator": "FRD-VELOCITY-INDICATOR-001",
    "duplicate_indicator": "FRD-DUPLICATE-INDICATOR-001",
    "amount_outlier_indicator": "FRD-AMOUNT-INDICATOR-001",
    "identity_consistency_indicator": "FRD-IDENTITY-INDICATOR-001",
}


def matched_rule_ids(features: dict[str, object]) -> list[str]:
    matches = [rule_id for field, rule_id in SIGNAL_RULES.items() if bool(features.get(field))]
    signal_count = len(matches)
    if signal_count >= 2:
        matches.append("FRD-COMPOUND-INDICATOR-001")
    if signal_count >= 3:
        matches.append("FRD-HIGH-PRIORITY-INDICATOR-001")
    return matches


def result_for_rule(rule_id: str) -> tuple[int, str, str]:
    if rule_id == "FRD-HIGH-PRIORITY-INDICATOR-001":
        return 80, "HIGH", "FR3"
    if rule_id == "FRD-COMPOUND-INDICATOR-001":
        return 55, "MEDIUM", "FR2"
    return 25, "LOW", "FR1"
