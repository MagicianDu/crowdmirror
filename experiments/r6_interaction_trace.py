from __future__ import annotations

from typing import Any

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, rounded_distribution, write_json_artifact


R6_INTERACTION_TRACE_SCHEMA_VERSION = "r6-interaction-trace-v1"


def build_r6_interaction_trace(
    *,
    artifact_id: str,
    run_id: str,
    prior_manifest: dict[str, Any],
    scenario_manifest: dict[str, Any],
    rounds: int = 3,
    interaction_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    static_prior = prior_manifest["aggregate_static_response_prior"]
    profile = interaction_profile or _default_interaction_profile()
    delta = dict(profile["delta_distribution"])
    interaction_result = rounded_distribution(
        {option: static_prior[option] + delta[option] for option in static_prior},
        digits=2,
    )
    events = _events(rounds=rounds)
    manifest = {
        "schema_version": R6_INTERACTION_TRACE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "overall_status": "passed",
        "source_prior_manifest_id": prior_manifest["artifact_id"],
        "source_scenario_manifest_id": scenario_manifest["artifact_id"],
        "rounds": rounds,
        "event_count": len(events),
        "events": events,
        "static_prior_distribution": static_prior,
        "interaction_result_distribution": interaction_result,
        "delta_distribution": delta,
        "segment_shifts": list(profile["segment_shifts"]),
        "source_refs": _source_refs(prior_manifest, scenario_manifest),
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": ["interaction_shift_requires_outcome_validation"],
        "blocking_gaps": [],
    }
    assert_strict_json(manifest)
    return manifest


def write_r6_interaction_trace(output: str, **kwargs: Any):
    return write_json_artifact(output, build_r6_interaction_trace(**kwargs))


def _default_interaction_profile() -> dict[str, Any]:
    return {
        "delta_distribution": {"accept": -0.04, "neutral": -0.03, "reject": 0.07},
        "segment_shifts": [
            {
                "segment_id": "sensitive_low_trust",
                "mechanisms": [
                    "fairness_concern",
                    "peer_amplification",
                    "substitution_pressure",
                ],
                "delta_distribution": {"accept": -0.07, "neutral": -0.05, "reject": 0.12},
            },
            {
                "segment_id": "pragmatic_switchers",
                "mechanisms": ["substitution_pressure"],
                "delta_distribution": {"accept": -0.04, "neutral": -0.02, "reject": 0.06},
            },
            {
                "segment_id": "stable_high_trust",
                "mechanisms": ["official_trust_buffer"],
                "delta_distribution": {"accept": -0.01, "neutral": -0.01, "reject": 0.02},
            },
        ],
    }


def _events(*, rounds: int) -> list[dict[str, Any]]:
    events = []
    mechanisms = [
        "official_exposure",
        "fairness_concern_contagion",
        "substitution_discussion",
        "peer_amplification",
        "trust_buffer",
        "complaint_visibility",
    ]
    for index, mechanism in enumerate(mechanisms):
        events.append(
            {
                "round": min(index // 2 + 1, rounds),
                "source_segment": "stable_high_trust" if index % 2 == 0 else "sensitive_low_trust",
                "target_segment": "sensitive_low_trust" if index % 2 == 0 else "pragmatic_switchers",
                "channel": "official" if index == 0 else "social_discussion",
                "mechanism": mechanism,
            }
        )
    return events


def _source_refs(prior_manifest: dict[str, Any], scenario_manifest: dict[str, Any]) -> list[str]:
    refs = [prior_manifest["artifact_id"], scenario_manifest["artifact_id"]]
    refs.extend(prior_manifest.get("source_refs", []))
    refs.extend(scenario_manifest.get("source_refs", []))
    return list(dict.fromkeys(refs))
