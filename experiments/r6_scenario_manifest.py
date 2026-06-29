from __future__ import annotations

from typing import Any

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    risk_flags,
    source_refs,
    write_json_artifact,
)


R6_SCENARIO_MANIFEST_SCHEMA_VERSION = "r6-scenario-manifest-v1"


def build_r6_scenario_manifest(
    *,
    artifact_id: str,
    run_id: str,
    scenario: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    scenario_payload = scenario or _default_scenario()
    manifest = {
        "schema_version": R6_SCENARIO_MANIFEST_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "passed",
        "scenario_id": non_empty_string(
            scenario_payload.get("scenario_id"),
            field="scenario_id",
        ),
        "industry_binding": "generic",
        "change_type": non_empty_string(scenario_payload.get("change_type"), field="change_type"),
        "impact_dimensions": _non_empty_string_list(
            scenario_payload.get("impact_dimensions"),
            field="impact_dimensions",
        ),
        "communication_plan": _communication_plan(scenario_payload.get("communication_plan")),
        "alternative_scenarios": _non_empty_string_list(
            scenario_payload.get("alternative_scenarios"),
            field="alternative_scenarios",
        ),
        "source_refs": source_refs(
            scenario_payload.get("source_refs", ["fixture:generic_change_scenario"])
        ),
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": risk_flags(
            scenario_payload.get("risk_flags", ["scenario_is_assumption_until_outcome_available"])
        ),
        "blocking_gaps": [],
    }
    assert_strict_json(manifest)
    return manifest


def write_r6_scenario_manifest(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_scenario_manifest(**kwargs))


def _default_scenario() -> dict[str, Any]:
    return {
        "scenario_id": "generic_price_change_001",
        "change_type": "price",
        "impact_dimensions": [
            "cost_increase",
            "fairness_concern",
            "substitution_pressure",
        ],
        "communication_plan": {
            "source": "official",
            "message_frame": "cost_pass_through",
            "mitigation": "loyalty_compensation",
        },
        "alternative_scenarios": ["no_compensation", "phased_release"],
        "source_refs": ["fixture:generic_change_scenario"],
    }


def _communication_plan(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("communication_plan must be an object")
    return {
        "source": non_empty_string(value.get("source"), field="communication_plan.source"),
        "message_frame": non_empty_string(
            value.get("message_frame"),
            field="communication_plan.message_frame",
        ),
        "mitigation": non_empty_string(
            value.get("mitigation"),
            field="communication_plan.mitigation",
        ),
    }


def _non_empty_string_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    return [non_empty_string(item, field=f"{field}[{index}]") for index, item in enumerate(value)]
