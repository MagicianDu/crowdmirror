from __future__ import annotations

from typing import Any

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact


R6_RISK_SHIFT_REPORT_SCHEMA_VERSION = "r6-risk-shift-report-v1"


def build_r6_risk_shift_report(
    *,
    artifact_id: str,
    run_id: str,
    prior_manifest: dict[str, Any],
    interaction_trace: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    static_reject = interaction_trace["static_prior_distribution"]["reject"]
    interaction_reject = interaction_trace["interaction_result_distribution"]["reject"]
    top_segments = sorted(
        interaction_trace["segment_shifts"],
        key=lambda segment: segment["delta_distribution"]["reject"],
        reverse=True,
    )
    report = {
        "schema_version": R6_RISK_SHIFT_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "passed",
        "source_prior_manifest_id": prior_manifest["artifact_id"],
        "source_interaction_trace_id": interaction_trace["artifact_id"],
        "overall_static_reject_rate": static_reject,
        "overall_interaction_reject_rate": interaction_reject,
        "delta": round(interaction_reject - static_reject, 2),
        "top_risk_segments": [
            {
                "segment_id": segment["segment_id"],
                "delta_reject": segment["delta_distribution"]["reject"],
                "mechanisms": segment["mechanisms"],
            }
            for segment in top_segments
        ],
        "recommended_observations": [
            "complaint_rate_by_segment",
            "observed_reject_proxy_by_segment",
            "negative_sentiment_rate",
            "conversion_delta",
        ],
        "source_refs": [
            prior_manifest["artifact_id"],
            interaction_trace["artifact_id"],
        ],
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": ["risk_hypothesis_not_validated_outcome"],
        "blocking_gaps": [],
    }
    assert_strict_json(report)
    return report


def write_r6_risk_shift_report(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_risk_shift_report(**kwargs))
