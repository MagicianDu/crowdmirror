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
from experiments.r6_outcome_holdout_registry import (
    R6_OUTCOME_HOLDOUT_REGISTRY_SCHEMA_VERSION,
    build_r6_outcome_holdout_registry,
)
from experiments.r6_theory_framework import (
    R6_THEORY_FRAMEWORK_SCHEMA_VERSION,
    build_r6_theory_framework,
)


R6_BEHAVIORAL_UPDATE_OPERATOR_V2_SCHEMA_VERSION = (
    "r6-behavioral-update-operator-v2"
)
R6_BEHAVIORAL_UPDATE_OPERATOR_V2_STATUS = (
    "operator_v2_structured_blocked_missing_holdout"
)
R6_OPERATOR_V2_BLOCKING_GAPS = [
    "needs_independent_same_family_operator_holdout",
    "needs_signal_validity_holdout_validation",
    "needs_real_or_field_outcome_proxy",
]


def build_r6_behavioral_update_operator_v2(
    *,
    artifact_id: str,
    run_id: str,
    holdout_registry: dict[str, Any] | None = None,
    theory_framework: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    if holdout_registry is None:
        holdout_registry = build_r6_outcome_holdout_registry(
            artifact_id=f"{artifact_id}-outcome-holdout-registry",
            run_id=run_id,
        )
    if theory_framework is None:
        theory_framework = build_r6_theory_framework(
            artifact_id=f"{artifact_id}-theory-framework",
            run_id=run_id,
        )
    if not isinstance(holdout_registry, dict):
        raise ValueError("holdout_registry must be a JSON object")
    if not isinstance(theory_framework, dict):
        raise ValueError("theory_framework must be a JSON object")
    _validate_holdout_registry(holdout_registry)
    _validate_theory_framework(theory_framework)

    candidate_updates = _build_candidate_updates()
    report = {
        "schema_version": R6_BEHAVIORAL_UPDATE_OPERATOR_V2_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": R6_BEHAVIORAL_UPDATE_OPERATOR_V2_STATUS,
        "runtime_default_allowed": False,
        "operator_v2_summary": {
            "candidate_update_count": len(candidate_updates),
            "same_case_repair_count": sum(
                1
                for candidate in candidate_updates
                if candidate["candidate_scope"] == "same_case_repair"
            ),
            "transfer_candidate_count": sum(
                1
                for candidate in candidate_updates
                if candidate["candidate_scope"] == "transfer_candidate"
            ),
            "runtime_default_allowed_count": sum(
                1
                for candidate in candidate_updates
                if candidate["runtime_default_allowed"]
            ),
            "prompt_patch_update_count": sum(
                1 for candidate in candidate_updates if candidate["prompt_patch_text"]
            ),
        },
        "acceptance_gates": {
            "operator_v2_structured": True,
            "operator_v2_runtime_default_allowed": False,
            "independent_holdout_available": _independent_holdout_available(
                holdout_registry
            ),
            "signal_validity_holdout_validated": False,
            "real_or_field_outcome_proxy_available": False,
            "field_outcome_validated": False,
            "ccf_a_main_contribution_ready": False,
            "prompt_patch_absent": True,
        },
        "candidate_updates": candidate_updates,
        "blocking_gaps": R6_OPERATOR_V2_BLOCKING_GAPS,
        "source_refs": _source_refs(holdout_registry, theory_framework),
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Behavioral update operator v2 adds explicit error "
                "attribution and transfer preconditions, but remains blocked "
                "until independent same-family holdout, signal-validity "
                "holdout, and real or field outcome proxy evidence exist."
            ),
            (
                "These candidates are structured research diagnostics only; "
                "they are not prompt patches, field validation, CCF-A readiness, "
                "or Product runtime defaults."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "operator_v2_blocked_missing_independent_holdout",
            "signal_validity_holdout_missing",
            "field_outcome_proxy_missing",
            "not_runtime_default",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_behavioral_update_operator_v2(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_behavioral_update_operator_v2(**kwargs),
    )


def _build_candidate_updates() -> list[dict[str, Any]]:
    return [
        {
            "operator_family": "over_amplification_damping",
            "candidate_scope": "same_case_repair",
            "error_attribution": {
                "primary_component": "over_amplification",
                "secondary_components": [
                    "propagation_direction_error",
                    "outcome_mapping_noise",
                ],
                "attribution_status": "structured_needs_independent_holdout",
            },
            "target_segments": [
                "rights_rule_sensitive_segments",
                "static_prior_close_segments",
            ],
            "parameter_delta": {
                "amplification_cap_delta": -0.05,
                "static_prior_close_guard": 0.03,
            },
            "transfer_preconditions": [
                "independent_same_family_in_condition_holdout",
                "signal_validity_holdout_non_regression",
                "real_or_field_outcome_proxy",
            ],
            "acceptance_status": "blocked_missing_independent_holdout",
            "runtime_default_allowed": False,
            "prompt_patch_text": "",
        },
        {
            "operator_family": "under_diffusion_boost",
            "candidate_scope": "transfer_candidate",
            "error_attribution": {
                "primary_component": "under_diffusion",
                "secondary_components": [
                    "static_prior_miss",
                    "topology_mismatch",
                ],
                "attribution_status": "structured_needs_independent_holdout",
            },
            "target_segments": [
                "public_service_access_segments",
                "memory_threshold_sensitive_segments",
            ],
            "parameter_delta": {
                "diffusion_sensitivity_delta": 0.05,
                "memory_activation_threshold_delta": -0.1,
            },
            "transfer_preconditions": [
                "independent_same_family_in_condition_holdout",
                "signal_validity_holdout_non_regression",
                "real_or_field_outcome_proxy",
            ],
            "acceptance_status": "blocked_missing_independent_holdout",
            "runtime_default_allowed": False,
            "prompt_patch_text": "",
        },
        {
            "operator_family": "trust_modifier_reweighting",
            "candidate_scope": "transfer_candidate",
            "error_attribution": {
                "primary_component": "propagation_direction_error",
                "secondary_components": [
                    "topology_mismatch",
                    "outcome_mapping_noise",
                ],
                "attribution_status": "structured_needs_independent_holdout",
            },
            "target_segments": [
                "trust_mediated_peer_segments",
                "source_credibility_sensitive_segments",
            ],
            "parameter_delta": {
                "trusted_peer_weight_delta": 0.04,
                "unsupported_amplifier_weight_delta": -0.04,
            },
            "transfer_preconditions": [
                "independent_same_family_in_condition_holdout",
                "signal_validity_holdout_non_regression",
                "real_or_field_outcome_proxy",
            ],
            "acceptance_status": "blocked_missing_independent_holdout",
            "runtime_default_allowed": False,
            "prompt_patch_text": "",
        },
    ]


def _independent_holdout_available(holdout_registry: dict[str, Any]) -> bool:
    _validate_holdout_registry(holdout_registry)
    registry_summary = holdout_registry.get("registry_summary", {})
    return registry_summary["in_condition_independent_holdout_available"] is True


def _source_refs(
    holdout_registry: dict[str, Any],
    theory_framework: dict[str, Any],
) -> list[str]:
    refs = []
    for field, artifact in (
        ("holdout_registry", holdout_registry),
        ("theory_framework", theory_framework),
    ):
        refs.append(
            non_empty_string(
                artifact.get("artifact_id"),
                field=f"{field}.artifact_id",
            )
        )
    return list(dict.fromkeys(refs))


def _validate_holdout_registry(holdout_registry: dict[str, Any]) -> None:
    _require_exact(
        holdout_registry,
        field="holdout_registry.schema_version",
        expected=R6_OUTCOME_HOLDOUT_REGISTRY_SCHEMA_VERSION,
    )
    _require_exact(
        holdout_registry,
        field="holdout_registry.status",
        expected="holdout_registry_ready_missing_required_slots",
    )
    non_empty_string(
        holdout_registry.get("artifact_id"),
        field="holdout_registry.artifact_id",
    )
    acceptance_gates = _require_object(
        holdout_registry.get("acceptance_gates"),
        field="holdout_registry.acceptance_gates",
    )
    _require_false(
        acceptance_gates,
        field="holdout_registry.acceptance_gates.runtime_default_allowed",
    )
    _require_false(
        acceptance_gates,
        field="holdout_registry.acceptance_gates.ccf_a_main_contribution_ready",
    )
    _require_false(
        acceptance_gates,
        field="holdout_registry.acceptance_gates.field_outcome_validated",
    )
    registry_summary = _require_object(
        holdout_registry.get("registry_summary"),
        field="holdout_registry.registry_summary",
    )
    availability = registry_summary.get("in_condition_independent_holdout_available")
    if not isinstance(availability, bool):
        raise ValueError(
            "holdout_registry.registry_summary."
            "in_condition_independent_holdout_available must be a boolean"
        )


def _validate_theory_framework(theory_framework: dict[str, Any]) -> None:
    _require_exact(
        theory_framework,
        field="theory_framework.schema_version",
        expected=R6_THEORY_FRAMEWORK_SCHEMA_VERSION,
    )
    _require_exact(
        theory_framework,
        field="theory_framework.status",
        expected="theory_framework_ready",
    )
    non_empty_string(
        theory_framework.get("artifact_id"),
        field="theory_framework.artifact_id",
    )
    acceptance_gates = _require_object(
        theory_framework.get("acceptance_gates"),
        field="theory_framework.acceptance_gates",
    )
    _require_false(
        acceptance_gates,
        field="theory_framework.acceptance_gates.runtime_default_allowed",
    )
    _require_false(
        acceptance_gates,
        field="theory_framework.acceptance_gates.field_outcome_validated",
    )


def _require_object(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a JSON object")
    return value


def _require_exact(
    artifact: dict[str, Any],
    *,
    field: str,
    expected: str,
) -> None:
    key = field.rsplit(".", maxsplit=1)[-1]
    if artifact.get(key) != expected:
        raise ValueError(f"{field} must be {expected}")


def _require_false(artifact: dict[str, Any], *, field: str) -> None:
    key = field.rsplit(".", maxsplit=1)[-1]
    if artifact.get(key) is not False:
        raise ValueError(f"{field} must be False")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_behavioral_update_operator_v2(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
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
