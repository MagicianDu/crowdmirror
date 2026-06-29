from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_mechanism_propagation_trace import (
    build_r6_mechanism_propagation_trace,
)


R6_BEHAVIORAL_UPDATE_OPERATOR_SCHEMA_VERSION = (
    "r6-behavioral-update-operator-v1"
)


def build_r6_behavioral_update_operator(
    artifact_id: str,
    run_id: str,
    propagation_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if propagation_trace is None:
        propagation_trace = build_r6_mechanism_propagation_trace(
            artifact_id=f"{artifact_id}-mechanism-propagation-trace",
            run_id=run_id,
        )
    if not isinstance(propagation_trace, dict):
        raise ValueError("propagation_trace must be a JSON object")

    candidate_updates = _build_candidate_updates(propagation_trace)
    _validate_candidate_provenance(candidate_updates)
    prompt_patch_update_count = sum(
        1 for update in candidate_updates if update["prompt_patch_text"]
    )
    runtime_default_allowed_count = sum(
        1 for update in candidate_updates if update["runtime_default_allowed"]
    )
    report = {
        "schema_version": R6_BEHAVIORAL_UPDATE_OPERATOR_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "behavioral_update_candidate_blocked_pending_holdout",
        "runtime_default_allowed": False,
        "operator_summary": {
            "candidate_update_count": len(candidate_updates),
            "prompt_patch_update_count": prompt_patch_update_count,
            "runtime_default_allowed_count": runtime_default_allowed_count,
            "structured_operator_update_count": len(candidate_updates)
            - prompt_patch_update_count,
            "field_outcome_validated": False,
        },
        "acceptance_gates": {
            "operator_update_structured": bool(candidate_updates),
            "prompt_patch_absent": prompt_patch_update_count == 0,
            "runtime_default_allowed": False,
            "operator_holdout_validated": False,
            "product_guard_required": True,
        },
        "candidate_updates": candidate_updates,
        "source_refs": _source_refs(propagation_trace),
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Behavioral update operator is a structured diagnostic "
                "candidate only; it is not a prompt patch, not field "
                "validation, and not runtime default behavior."
            ),
            (
                "Product failure diagnosis, false-alarm gate, claim boundary, "
                "and evidence-card guard remain required for every candidate."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "operator_update_not_runtime_default",
            "operator_holdout_missing",
            "field_outcome_validation_missing",
            "product_guard_required",
        ],
        "blocking_gaps": [
            "needs_operator_holdout_validation",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_behavioral_update_operator(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r6_behavioral_update_operator(**kwargs))


def _build_candidate_updates(
    propagation_trace: dict[str, Any],
) -> list[dict[str, Any]]:
    rights_paths = _dynamic_path_refs(
        propagation_trace,
        case_id="generic-rights-rule-change",
        path_type="peer_amplified_risk_diffusion",
    )
    service_paths = _dynamic_path_refs(
        propagation_trace,
        case_id="generic-public-service-policy-change",
        path_type="memory_threshold_activation",
    )
    return [
        {
            "operator_id": "damp-rights-rule-over-amplification",
            "update_target": "cap_or_damping_rule",
            "parameter_delta": {
                "max_reject_delta_when_static_prior_close": 0.02,
                "static_prior_close_error_threshold": 0.03,
            },
            "affected_segments": _affected_segments(rights_paths),
            "source_dynamic_paths": rights_paths,
            "derived_from_failure_boundary": (
                "interaction_over_amplifies_rejection_risk"
            ),
            "expected_repair": (
                "Damp rejection amplification for rights or rule changes when "
                "the static prior is already close to observed bounded proxy "
                "outcomes."
            ),
            "new_false_alarm_risk": (
                "Could suppress real rights or rule-change diffusion if the "
                "close-static-prior condition is not independently validated."
            ),
            "runtime_decision": "blocked_pending_operator_holdout",
            "runtime_default_allowed": False,
            "prompt_patch_text": "",
        },
        {
            "operator_id": "boost-service-access-memory-activation",
            "update_target": "activation_threshold",
            "parameter_delta": {
                "memory_activation_threshold_delta": -0.1,
                "min_peer_amplified_path_count": 1,
            },
            "affected_segments": _affected_segments(service_paths),
            "source_dynamic_paths": service_paths,
            "derived_from_failure_boundary": (
                "static_prior_miss_under_interaction_diffusion"
            ),
            "expected_repair": (
                "Increase memory-threshold activation sensitivity for service "
                "access disruption paths that the static prior under-expresses."
            ),
            "new_false_alarm_risk": (
                "Could over-trigger service access risk when peer amplification "
                "is fixture-specific rather than outcome-validated."
            ),
            "runtime_decision": "blocked_pending_operator_holdout",
            "runtime_default_allowed": False,
            "prompt_patch_text": "",
        },
    ]


def _dynamic_path_refs(
    propagation_trace: dict[str, Any],
    *,
    case_id: str,
    path_type: str,
) -> list[dict[str, Any]]:
    refs = []
    for case_trace in propagation_trace.get("case_traces", []):
        if case_trace.get("case_id") != case_id:
            continue
        for dynamic_path in case_trace.get("dynamic_paths", []):
            if dynamic_path.get("path_type") != path_type:
                continue
            refs.append(
                {
                    "source_key": case_trace["source_key"],
                    "case_id": case_trace["case_id"],
                    "path_type": dynamic_path["path_type"],
                    "rounds": dynamic_path["rounds"],
                    "source_segment_id": dynamic_path["source_segment_id"],
                    "target_segment_id": dynamic_path["target_segment_id"],
                    "mechanism_sequence": dynamic_path["mechanism_sequence"],
                }
            )
    return refs


def _validate_candidate_provenance(candidate_updates: list[dict[str, Any]]) -> None:
    if any(
        not update["source_dynamic_paths"] or not update["affected_segments"]
        for update in candidate_updates
    ):
        raise ValueError(
            "propagation_trace lacks required dynamic paths for behavioral "
            "update operator"
        )


def _affected_segments(dynamic_paths: list[dict[str, Any]]) -> list[str]:
    segment_ids = []
    for dynamic_path in dynamic_paths:
        segment_ids.append(dynamic_path["source_segment_id"])
        segment_ids.append(dynamic_path["target_segment_id"])
    return list(dict.fromkeys(segment_ids))


def _source_refs(propagation_trace: dict[str, Any]) -> list[str]:
    refs = []
    artifact_id = propagation_trace.get("artifact_id")
    if artifact_id:
        refs.append(str(artifact_id))
    refs.extend(str(ref) for ref in propagation_trace.get("source_refs", []))
    return list(dict.fromkeys(refs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_behavioral_update_operator(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "candidate_update_count": report["operator_summary"][
                    "candidate_update_count"
                ],
                "output": str(output_path),
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
