from __future__ import annotations

from typing import Any

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact


R6_OUTCOME_MANIFEST_SCHEMA_VERSION = "r6-outcome-manifest-v1"


def build_r6_outcome_manifest(
    *,
    artifact_id: str,
    run_id: str,
    outcome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    outcome_payload = _default_outcome()
    if outcome:
        outcome_payload.update(outcome)
        if "metrics" in outcome:
            outcome_payload["metrics"] = {**_default_outcome()["metrics"], **outcome["metrics"]}
        if "by_segment" in outcome:
            outcome_payload["by_segment"] = outcome["by_segment"]
    manifest = {
        "schema_version": R6_OUTCOME_MANIFEST_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "passed",
        "release_id": non_empty_string(outcome_payload["release_id"], field="release_id"),
        "observation_window": non_empty_string(
            outcome_payload["observation_window"],
            field="observation_window",
        ),
        "metrics": dict(outcome_payload["metrics"]),
        "by_segment": dict(outcome_payload["by_segment"]),
        "source_refs": list(outcome_payload["source_refs"]),
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": list(outcome_payload["risk_flags"]),
        "data_quality_flags": list(outcome_payload["data_quality_flags"]),
        "blocking_gaps": [],
    }
    assert_strict_json(manifest)
    return manifest


def write_r6_outcome_manifest(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_outcome_manifest(**kwargs))


def _default_outcome() -> dict[str, Any]:
    return {
        "release_id": "generic_release_001",
        "observation_window": "release_plus_14_days",
        "metrics": {
            "observed_reject_proxy": 0.41,
            "complaint_rate": 0.042,
            "negative_sentiment_rate": 0.36,
            "conversion_delta": -0.11,
        },
        "by_segment": {
            "sensitive_low_trust": {
                "observed_reject_proxy": 0.56,
                "observed_behavior_change_proxy": 0.18,
            },
            "stable_high_trust": {
                "observed_reject_proxy": 0.18,
                "observed_behavior_change_proxy": 0.04,
            },
            "pragmatic_switchers": {
                "observed_reject_proxy": 0.43,
                "observed_behavior_change_proxy": 0.11,
            },
        },
        "source_refs": ["fixture:post_release_proxy_metrics"],
        "risk_flags": ["outcome_proxy_not_direct_attitude_truth"],
        "data_quality_flags": ["proxy_metric_not_direct_attitude"],
    }
