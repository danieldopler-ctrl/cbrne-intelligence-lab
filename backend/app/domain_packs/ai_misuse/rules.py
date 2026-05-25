RULE_SET_VERSION = "AI_MISUSE_V0.1"

DEFAULT_RULES = [
    {
        "rule_id": "AIM-DUAL-USE-REVIEW-001",
        "title": "Ambiguous sensitive-domain request",
        "rationale": "Routes an ambiguous sensitive-domain case for analyst review without inferring harmful intent.",
        "severity": "LOW",
        "logic_config": {"review_level": "MR1", "intent_context": "AMBIGUOUS"},
    },
    {
        "rule_id": "AIM-CAPABILITY-UPLIFT-001",
        "title": "Restricted-assistance signal",
        "rationale": "Routes a described request for prohibited hazardous capability uplift to safety review.",
        "severity": "HIGH",
        "logic_config": {
            "review_level": "MR2",
            "assistance_types": ["CAPABILITY_UPLIFT", "OPERATIONAL_OPTIMIZATION"],
        },
    },
    {
        "rule_id": "AIM-SAFEGUARD-EVASION-001",
        "title": "Safeguard-evasion signal",
        "rationale": "Routes a described attempt to bypass safety controls for urgent internal review.",
        "severity": "HIGH",
        "logic_config": {"review_level": "MR3", "safeguard_evasion": True},
    },
    {
        "rule_id": "AIM-CONCEALMENT-001",
        "title": "Concealment or oversight-avoidance signal",
        "rationale": "Routes a described attempt to conceal restricted intent from safety review.",
        "severity": "HIGH",
        "logic_config": {"review_level": "MR3", "concealment_or_detection_avoidance": True},
    },
    {
        "rule_id": "AIM-TOOL-ENABLEMENT-001",
        "title": "Tool-enabled restricted-assistance signal",
        "rationale": "Raises priority where a high-risk case includes delegated tool or agent action.",
        "severity": "HIGH",
        "logic_config": {"review_level": "MR3", "tool_or_agent_enablement": True},
    },
    {
        "rule_id": "AIM-COMPOUND-RISK-001",
        "title": "Compound AI misuse risk signal",
        "rationale": "Raises priority when multiple restricted-assistance or evasion signals occur together.",
        "severity": "HIGH",
        "logic_config": {"review_level": "MR3", "minimum_high_risk_signals": 2},
    },
]


def matched_rule_ids(features: dict[str, object]) -> list[str]:
    if not bool(features.get("cbrne_relevance")):
        return []
    matches: list[str] = []
    if features.get("intent_context") == "AMBIGUOUS":
        matches.append("AIM-DUAL-USE-REVIEW-001")
    assistance_type = features.get("assistance_type")
    if assistance_type in {"CAPABILITY_UPLIFT", "OPERATIONAL_OPTIMIZATION"}:
        matches.append("AIM-CAPABILITY-UPLIFT-001")
    if bool(features.get("safeguard_evasion")) or assistance_type == "SAFEGUARD_BYPASS":
        matches.append("AIM-SAFEGUARD-EVASION-001")
    if bool(features.get("concealment_or_detection_avoidance")):
        matches.append("AIM-CONCEALMENT-001")
    high_risk_matches = [rule_id for rule_id in matches if rule_id != "AIM-DUAL-USE-REVIEW-001"]
    if bool(features.get("tool_or_agent_enablement")) and high_risk_matches:
        matches.append("AIM-TOOL-ENABLEMENT-001")
    high_risk_matches = [rule_id for rule_id in matches if rule_id != "AIM-DUAL-USE-REVIEW-001"]
    if len(high_risk_matches) >= 2:
        matches.append("AIM-COMPOUND-RISK-001")
    return matches


def result_for_rule(rule_id: str) -> tuple[int, str, str]:
    if rule_id == "AIM-DUAL-USE-REVIEW-001":
        return 30, "LOW", "MR1"
    if rule_id == "AIM-CAPABILITY-UPLIFT-001":
        return 65, "HIGH", "MR2"
    return 85, "HIGH", "MR3"
