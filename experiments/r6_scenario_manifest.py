from __future__ import annotations

from typing import Any

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact


R6_SCENARIO_MANIFEST_SCHEMA_VERSION = "r6-scenario-manifest-v1"


def build_r6_scenario_manifest(*, artifact_id: str, run_id: str) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    manifest = {
        "schema_version": R6_SCENARIO_MANIFEST_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "passed",
        "scenario_id": "generic_price_change_001",
        "industry_binding": "generic",
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
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": ["scenario_is_assumption_until_outcome_available"],
        "blocking_gaps": [],
    }
    assert_strict_json(manifest)
    return manifest


def write_r6_scenario_manifest(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_scenario_manifest(**kwargs))

