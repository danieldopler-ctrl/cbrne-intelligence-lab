from collections import Counter, defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.domain_packs.cbrne.chem_hazmat_rules import (
    DEFAULT_RULES,
    RULE_SET_VERSION,
    consequence_result,
    count_consequence_results,
    potential_release_result,
    reported_liquid_release_result,
    substance_result,
)
from app.domain_packs.cbrne.epa_rmp_toxic_substances import EPA_RMP_TOXIC_REFERENCE_URL
from app.models import Alert, AlertEvidence, DetectionRule, DetectionRun, Indicator, NormalizedEvent


def ensure_rules(db: Session) -> dict[str, DetectionRule]:
    rules = {
        rule.rule_id: rule
        for rule in db.scalars(
            select(DetectionRule).where(DetectionRule.version == RULE_SET_VERSION)
        ).all()
    }
    for rule_data in DEFAULT_RULES:
        if rule_data["rule_id"] not in rules:
            rule = DetectionRule(
                domain_pack="CBRNE_CHEM", version=RULE_SET_VERSION, active=True, **rule_data
            )
            db.add(rule)
            db.flush()
            rules[rule.rule_id] = rule
    return rules


def create_alert(
    db: Session,
    run: DetectionRun,
    rule: DetectionRule,
    event: NormalizedEvent,
    *,
    score: int,
    priority: str,
    recommended_level: str,
    label: str,
    rationale: str,
    evidence: dict,
    additional_evidence_events: list[NormalizedEvent] | None = None,
) -> Alert:
    indicator = Indicator(
        event_id=event.id,
        detection_run_id=run.id,
        detection_rule_id=rule.id,
        evidence=evidence,
        indicator_score=score,
    )
    db.add(indicator)
    db.flush()
    alert = Alert(
        detection_run_id=run.id,
        title=f"{rule.title}: {event.source_record_id}",
        priority=priority,
        result_label=label,
        score=score,
        confidence="SOURCE_DERIVED",
        recommended_threat_level=recommended_level,
        rationale=rationale,
    )
    db.add(alert)
    db.flush()
    db.add(AlertEvidence(alert_id=alert.id, event_id=event.id, indicator_id=indicator.id))
    for related_event in additional_evidence_events or []:
        if related_event.id != event.id:
            db.add(AlertEvidence(alert_id=alert.id, event_id=related_event.id, indicator_id=indicator.id))
    record_audit(db, "ALERT_CREATED", "alert", alert.id, metadata={"rule_id": rule.rule_id})
    return alert


def run_detection(
    db: Session, ingest_batch_id: int | None, *, include_observations: bool = False
) -> DetectionRun:
    rules = ensure_rules(db)
    query = select(NormalizedEvent)
    if ingest_batch_id is not None:
        query = query.where(NormalizedEvent.ingest_batch_id == ingest_batch_id)
    events = db.scalars(query).all()
    run = DetectionRun(
        ingest_batch_id=ingest_batch_id,
        domain_pack="CBRNE_CHEM",
        rule_set_version=RULE_SET_VERSION,
        event_count=len(events),
    )
    db.add(run)
    db.flush()
    alert_count = 0
    chemical_events = [event for event in events if event.hazard_domain == "CHEM"]
    incident_groups: dict[tuple[int, str], list[NormalizedEvent]] = defaultdict(list)
    for event in chemical_events:
        incident_groups[(event.source_id, event.source_record_id)].append(event)

    for (_, incident_id), incident_events in incident_groups.items():
        is_count_bearing = any(
            (event.severity_features or {}).get("source_capability") == "count_bearing"
            for event in incident_events
        )
        if is_count_bearing:
            count_features: dict[str, object] = {
                "source_capability": "count_bearing",
                "injuries_count": max(
                    int((event.severity_features or {}).get("injuries_count", 0) or 0)
                    for event in incident_events
                ),
                "fatalities_count": max(
                    int((event.severity_features or {}).get("fatalities_count", 0) or 0)
                    for event in incident_events
                ),
                "evacuations_count": max(
                    int((event.severity_features or {}).get("evacuations_count", 0) or 0)
                    for event in incident_events
                ),
                "incident_rows_evaluated": len(incident_events),
            }
            for rule_id, score, priority, level in count_consequence_results(count_features):
                create_alert(
                    db,
                    run,
                    rules[rule_id],
                    incident_events[0],
                    score=score,
                    priority=priority,
                    recommended_level=level,
                    label="INDICATOR",
                    rationale=(
                        "NRC reports count-bearing consequence data that exceeds the documented "
                        "review threshold. Counts are evaluated once per NRC report."
                    ),
                    evidence={"incident_id": incident_id, **count_features},
                )
                alert_count += 1
            if int(count_features["fatalities_count"]) > 0:
                score, priority, level = consequence_result(
                    {"fatalities": count_features["fatalities_count"], "injuries": 0, "evacuated": 0}
                )
                create_alert(
                    db,
                    run,
                    rules["CHEM-CONSEQUENCE-001"],
                    incident_events[0],
                    score=score,
                    priority=priority,
                    recommended_level=level,
                    label="INDICATOR",
                    rationale="NRC report includes one or more reported fatalities.",
                    evidence={"incident_id": incident_id, **count_features},
                )
                alert_count += 1
            continue
        consequence_features: dict[str, object] = {
            "fatalities": max(int((event.severity_features or {}).get("fatalities", 0) or 0) for event in incident_events),
            "injuries": max(int((event.severity_features or {}).get("injuries", 0) or 0) for event in incident_events),
            "evacuated": max(int((event.severity_features or {}).get("evacuated", 0) or 0) for event in incident_events),
            "incident_rows_evaluated": len(incident_events),
        }
        if any(
            (event.severity_features or {}).get("consequence_basis")
            == "binary_indicators_with_numeric_fatalities"
            for event in incident_events
        ):
            consequence_features["consequence_basis"] = "binary_indicators_with_numeric_fatalities"
        result = consequence_result(consequence_features)
        if result:
            score, priority, level = result
            basis_note = (
                " Binary injury or serious-evacuation indicators establish presence only, not counts."
                if consequence_features.get("consequence_basis") == "binary_indicators_with_numeric_fatalities"
                else ""
            )
            create_alert(
                db,
                run,
                rules["CHEM-CONSEQUENCE-001"],
                incident_events[0],
                score=score,
                priority=priority,
                recommended_level=level,
                label="INDICATOR",
                rationale=(
                    "Source-reported consequence fields exceed the documented review threshold. "
                    "One alert is created per source incident identifier." + basis_note
                ),
                evidence={"incident_id": incident_id, **consequence_features},
            )
            alert_count += 1

    liquid_release_groups: dict[tuple[int, str, str], list[NormalizedEvent]] = defaultdict(list)
    for event in chemical_events:
        features = event.severity_features or {}
        if features.get("quantity_unit") == "LGA" and features.get("quantity_released_liquid_gallons") is not None:
            liquid_release_groups[
                (event.source_id, event.source_record_id, event.commodity or "Unspecified commodity")
            ].append(event)
        elif features.get("quantity_released_gallons") is not None:
            liquid_release_groups[
                (event.source_id, event.source_record_id, event.commodity or "Multiple materials")
            ].append(event)
    for (_, incident_id, commodity), release_events in liquid_release_groups.items():
        liquid_gallons = sum(
            float(
                (event.severity_features or {}).get(
                    "quantity_released_liquid_gallons",
                    (event.severity_features or {}).get("quantity_released_gallons", 0),
                )
                or 0
            )
            for event in release_events
        )
        release_result = reported_liquid_release_result(liquid_gallons)
        if release_result:
            score, priority, level = release_result
            create_alert(
                db,
                run,
                rules["CHEM-RELEASE-QUANTITY-001"],
                release_events[0],
                score=score,
                priority=priority,
                recommended_level=level,
                label="INDICATOR",
                rationale=(
                    "Source reports a large released liquid quantity in gallons or supported converted "
                    "liquid-volume units. This is not an intent finding."
                ),
                evidence={
                    "incident_id": incident_id,
                    "commodity": commodity,
                    "reported_liquid_release_gallons": liquid_gallons,
                    "quantity_unit": (
                        "LGA"
                        if (release_events[0].severity_features or {}).get("quantity_unit") == "LGA"
                        else "CONVERTED_TO_GALLONS"
                    ),
                    "rows_aggregated": len(release_events),
                    "conversion_approximate": any(
                        bool((event.severity_features or {}).get("quantity_gallons_approximate"))
                        for event in release_events
                    ),
                },
            )
            alert_count += 1

    recurrence_events = [
        event
        for event in chemical_events
        if (event.severity_features or {}).get("source_system") != "NRC"
    ]
    period_regions = Counter(
        (event.region, event.event_date[:7])
        for event in {
            (event.source_id, event.source_record_id): event
            for event in recurrence_events
            if event.region and event.event_date and len(event.event_date) >= 7
        }.values()
    )
    cluster_alerted: set[tuple[str, str]] = set()
    substance_alerted: set[tuple[str, str]] = set()
    for event in events:
        quantity_result = potential_release_result(event.severity_features or {})
        if event.hazard_domain == "CHEM" and quantity_result:
            score, priority, level = quantity_result
            create_alert(
                db,
                run,
                rules["CHEM-POTENTIAL-RELEASE-001"],
                event,
                score=score,
                priority=priority,
                recommended_level=level,
                label="INDICATOR",
                rationale=(
                    "Source reports a large maximum potential release. Quantity is not confirmed "
                    "actual release and does not account for chemical-specific hazard."
                ),
                evidence={"maximum_potential_release_gallons": event.severity_features["quantity_released"]},
            )
            alert_count += 1
        commodities = (event.severity_features or {}).get("commodities") or [event.commodity]
        for commodity in commodities:
            substance_match = substance_result(commodity)
            if event.hazard_domain == "CHEM" and substance_match:
                score, priority, level, match = substance_match
                substance_key = (event.source_record_id, match.regulated_substance)
                if substance_key not in substance_alerted:
                    create_alert(
                        db,
                        run,
                        rules["CHEM-SUBSTANCE-001"],
                        event,
                        score=score,
                        priority=priority,
                        recommended_level=level,
                        label="INDICATOR",
                        rationale=(
                            "Source commodity text matches an EPA RMP regulated toxic substance. "
                            "This is a review priority signal, not a finding of intent, quantity, "
                            "release consequence, or regulatory applicability."
                        ),
                        evidence={
                            "incident_id": event.source_record_id,
                            "source_commodity": match.source_commodity,
                            "epa_rmp_toxic_substance": match.regulated_substance,
                            "match_method": match.match_method,
                            "reference": EPA_RMP_TOXIC_REFERENCE_URL,
                        },
                    )
                    alert_count += 1
                    substance_alerted.add(substance_key)
        if include_observations and event.hazard_domain == "CHEM" and "release" in event.event_type.lower():
            create_alert(
                db,
                run,
                rules["CHEM-RELEASE-001"],
                event,
                score=20,
                priority="LOW",
                recommended_level="TL1",
                label="OBSERVATION",
                rationale="Source record identifies a chemical or hazardous-material release.",
                evidence={"event_type": event.event_type, "hazard_domain": event.hazard_domain},
            )
            alert_count += 1
        cluster_key = (
            (event.region, event.event_date[:7])
            if event.region and event.event_date and len(event.event_date) >= 7
            else None
        )
        if (
            event.hazard_domain == "CHEM"
            and (event.severity_features or {}).get("source_system") != "NRC"
            and cluster_key
            and period_regions[cluster_key] >= 3
            and cluster_key not in cluster_alerted
        ):
            create_alert(
                db,
                run,
                rules["CHEM-RECURRENCE-001"],
                event,
                score=55,
                priority="MEDIUM",
                recommended_level="TL2",
                label="INDICATOR",
                rationale=(
                    "Three or more chemical records share the mapped reporting region and month. "
                    "Baseline calibration is required before labeling this pattern anomalous."
                ),
                evidence={
                    "region": cluster_key[0],
                    "calendar_month": cluster_key[1],
                    "cluster_count": period_regions[cluster_key],
                },
            )
            alert_count += 1
            cluster_alerted.add(cluster_key)

    if ingest_batch_id is not None:
        nrc_events = [
            event for event in chemical_events if (event.severity_features or {}).get("source_system") == "NRC"
        ]
        all_events = db.scalars(select(NormalizedEvent)).all()
        phmsa_events = list(
            {
                (event.source_id, event.source_record_id, event.event_date): event
                for event in all_events
                if (event.severity_features or {}).get("consequence_basis")
                == "binary_indicators_with_numeric_fatalities"
            }.values()
        )
        correlated_pairs: set[tuple[int, int]] = set()
        for nrc_event in nrc_events:
            nrc_state = _state_code(nrc_event.region)
            nrc_date = _date_value(nrc_event.event_date)
            if not nrc_state or not nrc_date:
                continue
            for phmsa_event in phmsa_events:
                if _state_code(phmsa_event.region) != nrc_state:
                    continue
                phmsa_date = _date_value(phmsa_event.event_date)
                if not phmsa_date or abs((nrc_date - phmsa_date).days) > 3:
                    continue
                shared_substances = _regulated_substances(nrc_event) & _regulated_substances(phmsa_event)
                if not shared_substances:
                    continue
                pair = (nrc_event.id, phmsa_event.id)
                if pair in correlated_pairs:
                    continue
                create_alert(
                    db,
                    run,
                    rules["CHEM-CORRELATION-001"],
                    nrc_event,
                    score=60,
                    priority="MEDIUM",
                    recommended_level="TL2",
                    label="CORRELATED_ALERT",
                    rationale=(
                        "NRC and PHMSA records share an EPA RMP toxic substance match and identify "
                        "reports in the same state within three days. Analyst review is required "
                        "to determine whether the reports describe the same incident."
                    ),
                    evidence={
                        "nrc_report_id": nrc_event.source_record_id,
                        "phmsa_report_id": phmsa_event.source_record_id,
                        "state": nrc_state,
                        "days_apart": abs((nrc_date - phmsa_date).days),
                        "shared_epa_rmp_toxic_substances": sorted(shared_substances),
                    },
                    additional_evidence_events=[phmsa_event],
                )
                alert_count += 1
                correlated_pairs.add(pair)
    run.alert_count = alert_count
    record_audit(db, "DETECTION_RUN_COMPLETED", "detection_run", run.id, metadata={"alerts": alert_count})
    db.commit()
    db.refresh(run)
    return run


def _state_code(region: str | None) -> str | None:
    if not region:
        return None
    candidate = region.strip().upper().split(",")[-1].strip()
    return candidate if len(candidate) == 2 and candidate.isalpha() else None


def _date_value(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _regulated_substances(event: NormalizedEvent) -> set[str]:
    commodities = (event.severity_features or {}).get("commodities") or [event.commodity]
    matches = [substance_result(commodity) for commodity in commodities]
    return {match[3].regulated_substance for match in matches if match}
