from __future__ import annotations

from typing import Any

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    claim_boundaries,
    non_empty_string,
    probability_distribution,
    rounded_distribution,
    risk_flags,
    source_refs,
    write_json_artifact,
)


R6_PRIOR_MANIFEST_SCHEMA_VERSION = "r6-prior-manifest-v1"
RESPONSE_OPTIONS = ["accept", "neutral", "reject"]


def build_r6_prior_manifest(
    *,
    artifact_id: str,
    run_id: str,
    segments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    segment_payloads = segments if segments is not None else _default_segments()
    validated_segments = [_validated_segment(segment) for segment in segment_payloads]
    aggregate = _aggregate_static_prior(validated_segments)
    manifest = {
        "schema_version": R6_PRIOR_MANIFEST_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "passed",
        "target_population": "generic_customer_or_public_group",
        "industry_binding": "generic",
        "response_options": RESPONSE_OPTIONS,
        "segment_axis": ["sensitivity", "trust", "substitution"],
        "segment_count": len(validated_segments),
        "segments": validated_segments,
        "aggregate_static_response_prior": aggregate,
        "no_interaction_control": {
            "enabled": True,
            "distribution": aggregate,
            "description": "Static prior without social exposure or interaction updates.",
        },
        "source_refs": ["fixture:generic_prior_segments"],
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "static_prior_not_dynamic_prediction",
            "not_accuracy_superiority_evidence",
        ],
        "blocking_gaps": [],
    }
    assert_strict_json(manifest)
    return manifest


def write_r6_prior_manifest(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_prior_manifest(**kwargs))


def _validated_segment(segment: dict[str, Any]) -> dict[str, Any]:
    segment_id = non_empty_string(segment.get("segment_id"), field="segment_id")
    weight = float(segment.get("weight"))
    if weight <= 0:
        raise ValueError("segment weight must be positive")
    static_response_prior = probability_distribution(
        segment.get("static_response_prior"),
        options=RESPONSE_OPTIONS,
        field=f"{segment_id}.static_response_prior",
    )
    refs = source_refs(segment.get("source_refs", ["fixture:generic_prior_segments"]))
    flags = risk_flags(segment.get("risk_flags", ["prior_fixture_for_r6_foundation"]))
    boundaries = claim_boundaries(segment.get("claim_boundaries", [R6_CLAIM_BOUNDARY]))
    return {
        "segment_id": segment_id,
        "weight": weight,
        "static_traits": dict(segment.get("static_traits", {})),
        "static_response_prior": static_response_prior,
        "uncertainty": float(segment.get("uncertainty", 0.12)),
        "source_refs": refs,
        "claim_boundaries": boundaries,
        "risk_flags": flags,
    }


def _aggregate_static_prior(segments: list[dict[str, Any]]) -> dict[str, float]:
    total_weight = sum(segment["weight"] for segment in segments)
    if total_weight <= 0:
        raise ValueError("segment weights must sum to a positive value")
    aggregate = {option: 0.0 for option in RESPONSE_OPTIONS}
    for segment in segments:
        for option in RESPONSE_OPTIONS:
            aggregate[option] += (
                segment["weight"] * segment["static_response_prior"][option] / total_weight
            )
    return rounded_distribution(aggregate, digits=2)


def _default_segments() -> list[dict[str, Any]]:
    return [
        {
            "segment_id": "sensitive_low_trust",
            "weight": 0.30,
            "static_traits": {
                "sensitivity": "high",
                "trust": "low",
                "substitution": "high",
            },
            "static_response_prior": {
                "accept": 0.28,
                "neutral": 0.25,
                "reject": 0.47,
            },
            "uncertainty": 0.18,
            "source_refs": ["fixture:segment_survey"],
        },
        {
            "segment_id": "stable_high_trust",
            "weight": 0.45,
            "static_traits": {
                "sensitivity": "low",
                "trust": "high",
                "substitution": "low",
            },
            "static_response_prior": {
                "accept": 0.65,
                "neutral": 0.25,
                "reject": 0.10,
            },
            "uncertainty": 0.10,
            "source_refs": ["fixture:segment_survey"],
        },
        {
            "segment_id": "pragmatic_switchers",
            "weight": 0.25,
            "static_traits": {
                "sensitivity": "medium",
                "trust": "medium",
                "substitution": "medium",
            },
            "static_response_prior": {
                "accept": 0.38,
                "neutral": 0.25,
                "reject": 0.37,
            },
            "uncertainty": 0.14,
            "source_refs": ["fixture:segment_survey"],
        },
    ]

