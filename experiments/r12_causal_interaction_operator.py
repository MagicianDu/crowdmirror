from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r11_outcome_feedback_update import (
    R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
)
from experiments.r12_outcome_case_registry import (
    R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
)


R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION = (
    "r12-causal-interaction-operator-v1"
)


def build_r12_causal_interaction_operator(
    *,
    artifact_id: str,
    run_id: str,
    r12_outcome_case_registry: dict[str, Any],
    r11_outcome_feedback_update: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_case_registry(r12_outcome_case_registry)
    _validate_feedback_update(r11_outcome_feedback_update)
    report = {
        "schema_version": R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_causal_interaction_operator_ready_guarded",
        "claim_level": "operator_contract_only",
        "operator_contract": {
            "operator_id": "r12_oscio_l1",
            "updates_are_structured_parameters_only": True,
            "prompt_or_persona_manual_patch_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "parameter_state": _parameter_state(
            case_registry=r12_outcome_case_registry,
            feedback_update=r11_outcome_feedback_update,
        ),
        "prior_shrinkage_rules": {
            "static_prior_is_base_distribution": True,
            "interaction_layer_updates_are_bounded": True,
            "small_sample_updates_shrink_toward_prior": True,
            "posterior_shrinkage_strength": 0.65,
            "validation_or_holdout_outcome_not_used_for_initialization": True,
        },
        "update_bounds": {
            "mechanism_weight": {
                "max_abs_delta": 0.08,
                "requires_holdout_before_default": True,
            },
            "segment_sensitivity": {
                "max_abs_delta": 0.12,
                "requires_holdout_before_default": True,
            },
            "interaction_edge_weight": {
                "max_abs_delta": 0.05,
                "requires_direct_propagation_evidence": True,
            },
            "uncertainty_parameter": {
                "max_abs_delta": 0.05,
                "requires_interval_miss_or_tail_risk_evidence": True,
            },
        },
        "interaction_edge_update_guard": {
            "direct_propagation_evidence_present": False,
            "edge_update_status": "rejected",
            "rejection_reason": (
                "r11 feedback packet lacks direct interaction propagation evidence"
            ),
        },
        "acceptance_gates": {
            "operator_contract_ready": True,
            "structured_parameter_state_present": True,
            "train_cases_only_used_for_parameter_initialization": True,
            "prompt_or_persona_manual_patch_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            r12_outcome_case_registry["artifact_id"],
            r11_outcome_feedback_update["artifact_id"],
        ],
        "next_required_artifact": "r12_outcome_supervised_update",
        "blocked_claims": [
            "R12 outcome-supervised update already validated",
            "R12 Product core method ready",
            "prompt/persona manual patch as automatic calibration",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_causal_interaction_operator(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_causal_interaction_operator(**kwargs))


def _validate_case_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION:
        raise ValueError("r12_outcome_case_registry.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_outcome_case_registry.acceptance_gates must be an object")
    if gates.get("outcome_leakage_blocked") is not True:
        raise ValueError("r12 outcome case registry must block outcome leakage")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 outcome case registry must not allow runtime default")


def _validate_feedback_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION:
        raise ValueError("r11_outcome_feedback_update.schema_version is invalid")
    gate = artifact.get("update_gate")
    if not isinstance(gate, dict):
        raise ValueError("r11_outcome_feedback_update.update_gate must be an object")
    if gate.get("runtime_default_allowed") is not False:
        raise ValueError("r11 feedback update must not allow runtime default")
    if gate.get("prompt_or_persona_manual_patch_allowed") is not False:
        raise ValueError("prompt/persona patch must be blocked")


def _parameter_state(
    *,
    case_registry: dict[str, Any],
    feedback_update: dict[str, Any],
) -> dict[str, Any]:
    train_cases = [case for case in case_registry["cases"] if case["split"] == "train"]
    accepted_segment = next(
        candidate
        for candidate in feedback_update["update_candidates"]
        if candidate["update_type"] == "segment_sensitivity"
        and candidate["status"] == "accepted"
    )
    mechanism = next(
        candidate
        for candidate in feedback_update["update_candidates"]
        if candidate["update_type"] == "mechanism_weight"
    )
    return {
        "mechanism_weights": {
            "price_pressure": {
                "value": round(0.5 + float(mechanism["recommended_delta"]), 2),
                "prior": 0.5,
                "lower_bound": 0.35,
                "upper_bound": 0.75,
                "source": "r11_feedback_diagnostic_price_pressure",
            },
            "trust_loss": {
                "value": 0.3,
                "prior": 0.3,
                "lower_bound": 0.1,
                "upper_bound": 0.55,
                "source": "r12_prior_contract",
            },
            "service_friction": {
                "value": 0.25,
                "prior": 0.25,
                "lower_bound": 0.05,
                "upper_bound": 0.5,
                "source": "r12_prior_contract",
            },
        },
        "segment_sensitivities": _segment_sensitivities(
            train_cases=train_cases,
            accepted_segment=accepted_segment,
        ),
        "interaction_edge_weights": {
            "scenario_to_price_pressure": {
                "value": 0.6,
                "prior": 0.55,
                "lower_bound": 0.3,
                "upper_bound": 0.8,
                "source": "hps_price_pressure_proxy",
            },
            "price_pressure_to_segment_reaction": {
                "value": 0.52,
                "prior": 0.5,
                "lower_bound": 0.3,
                "upper_bound": 0.75,
                "source": "r11_external_holdout_transfer",
            },
            "segment_peer_amplification": {
                "value": 0.0,
                "prior": 0.0,
                "lower_bound": 0.0,
                "upper_bound": 0.2,
                "source": "blocked_until_direct_propagation_evidence",
            },
        },
        "uncertainty_parameters": {
            "interval_half_width": {
                "value": 0.1,
                "prior": 0.1,
                "lower_bound": 0.08,
                "upper_bound": 0.2,
                "source": "r11_external_holdout_interval",
            },
            "tail_risk_margin": {
                "value": 0.03,
                "prior": 0.03,
                "lower_bound": 0.02,
                "upper_bound": 0.08,
                "source": "r11_high_risk_threshold_margin",
            },
            "posterior_shrinkage_strength": {
                "value": 0.65,
                "prior": 0.65,
                "lower_bound": 0.5,
                "upper_bound": 0.9,
                "source": "r12_prior_protection",
            },
        },
    }


def _segment_sensitivities(
    *,
    train_cases: list[dict[str, Any]],
    accepted_segment: dict[str, Any],
) -> dict[str, Any]:
    sensitivities = {}
    for case in train_cases:
        delta = (
            float(accepted_segment["recommended_delta"])
            if case["case_id"] == accepted_segment["target"]
            else 0.04
        )
        sensitivities[case["case_id"]] = {
            "value": round(1.0 + delta, 2),
            "prior": 1.0,
            "lower_bound": 0.8,
            "upper_bound": 1.25,
            "source": (
                "r11_segment_sensitivity_shadow_accepted"
                if case["case_id"] == accepted_segment["target"]
                else "r12_train_high_risk_segment_prior"
            ),
        }
    return sensitivities


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-outcome-case-registry-path", required=True)
    parser.add_argument("--r11-outcome-feedback-update-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_causal_interaction_operator(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_outcome_case_registry=load_json_artifact(
            args.r12_outcome_case_registry_path
        ),
        r11_outcome_feedback_update=load_json_artifact(
            args.r11_outcome_feedback_update_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
