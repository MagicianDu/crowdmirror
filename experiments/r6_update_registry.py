from __future__ import annotations

from typing import Any

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, R6_UPDATE_STATUSES, assert_strict_json, non_empty_string, write_json_artifact


R6_UPDATE_REGISTRY_SCHEMA_VERSION = "r6-update-registry-v1"


def build_r6_update_registry(
    *,
    artifact_id: str,
    run_id: str,
    learning_report: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    attribution = learning_report["error_attribution"][0]
    update = {
        "update_id": "r6-update-fairness-concern-001",
        "source_learning_report_id": learning_report["artifact_id"],
        "status": "diagnostic_only",
        "status_reason": "single outcome fixture; needs more outcomes before acceptance",
        "default_runtime_enabled": False,
        "recommended_update": attribution["recommended_update"],
        "rollback_condition": "any follow-up case regression or missing segment evidence",
    }
    if update["status"] not in R6_UPDATE_STATUSES:
        raise ValueError("invalid update status")
    registry = {
        "schema_version": R6_UPDATE_REGISTRY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "needs_more_outcomes",
        "source_learning_report_id": learning_report["artifact_id"],
        "updates": [update],
        "source_refs": [learning_report["artifact_id"]],
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": ["unvalidated_update_not_enabled"],
        "blocking_gaps": ["needs_more_outcomes_for_default_acceptance"],
    }
    assert_strict_json(registry)
    return registry


def write_r6_update_registry(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_update_registry(**kwargs))
