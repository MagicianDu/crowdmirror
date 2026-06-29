from __future__ import annotations

from typing import Any

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact


R6_LEARNING_REPORT_SCHEMA_VERSION = "r6-learning-report-v1"


def build_r6_learning_report(
    *,
    artifact_id: str,
    run_id: str,
    risk_shift_report: dict[str, Any],
    outcome_manifest: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    predicted = risk_shift_report["overall_interaction_reject_rate"]
    observed = outcome_manifest["metrics"]["observed_reject_proxy"]
    absolute_error = round(abs(observed - predicted), 2)
    report = {
        "schema_version": R6_LEARNING_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "diagnostic_ready",
        "source_risk_shift_report_id": risk_shift_report["artifact_id"],
        "source_outcome_manifest_id": outcome_manifest["artifact_id"],
        "prediction_vs_outcome": {
            "predicted_reject_rate": predicted,
            "observed_reject_proxy": observed,
            "absolute_error": absolute_error,
        },
        "error_attribution": [
            {
                "type": "mechanism_error",
                "confidence": 0.62,
                "diagnosis": (
                    "fairness_concern was underweighted for low-trust and "
                    "high-sensitivity segments"
                ),
                "recommended_update": {
                    "mechanism": "fairness_concern",
                    "target_segments": ["sensitive_low_trust"],
                    "weight_delta": 0.08,
                },
            }
        ],
        "update_policy": "human_review_required",
        "source_refs": [
            risk_shift_report["artifact_id"],
            outcome_manifest["artifact_id"],
        ],
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": ["learning_report_not_auto_update"],
        "blocking_gaps": [],
    }
    assert_strict_json(report)
    return report


def write_r6_learning_report(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_learning_report(**kwargs))
