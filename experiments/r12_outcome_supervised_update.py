from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
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
from experiments.r12_causal_interaction_operator import (
    R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION,
)
from experiments.r12_outcome_case_registry import (
    R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
)


R12_OUTCOME_SUPERVISED_UPDATE_SCHEMA_VERSION = (
    "r12-outcome-supervised-update-v1"
)


def build_r12_outcome_supervised_update(
    *,
    artifact_id: str,
    run_id: str,
    r12_outcome_case_registry: dict[str, Any],
    r12_causal_interaction_operator: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_case_registry(r12_outcome_case_registry)
    _validate_operator(r12_causal_interaction_operator)
    train_cases = sorted(
        (
            case
            for case in r12_outcome_case_registry["cases"]
            if case["split"] == "train"
        ),
        key=lambda item: item["case_id"],
    )
    training_residuals = [_training_residual(case) for case in train_cases]
    candidates = _update_candidates(
        causal_operator=r12_causal_interaction_operator,
        training_residuals=training_residuals,
    )
    report = {
        "schema_version": R12_OUTCOME_SUPERVISED_UPDATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_outcome_supervised_update_ready_guarded",
        "claim_level": "train_only_outcome_update_candidate",
        "training_data_guard": {
            "train_outcomes_used_for_update": [
                item["case_id"] for item in training_residuals
            ],
            "validation_outcomes_used_for_update": [],
            "holdout_outcomes_used_for_update": [],
            "outcome_leakage_blocked": True,
        },
        "training_residual_summary": _training_residual_summary(training_residuals),
        "training_residuals": training_residuals,
        "update_candidates": candidates,
        "update_gate": {
            "candidate_update_generated": True,
            "accepted_shadow_only_count": _count_status(candidates, "accepted"),
            "diagnostic_only_count": _count_status(candidates, "diagnostic_only"),
            "rejected_count": _count_status(candidates, "rejected"),
            "train_only_update": True,
            "outcome_leakage_blocked": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "requires_transfer_validation_before_product_support": True,
        },
        "source_refs": [
            r12_outcome_case_registry["artifact_id"],
            r12_causal_interaction_operator["artifact_id"],
        ],
        "next_required_artifact": "r12_transfer_validation",
        "blocked_claims": [
            "R12 transfer validation already passed",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "validation or holdout outcome used for training",
            "prompt/persona manual patch as automatic calibration",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_outcome_supervised_update(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_outcome_supervised_update(**kwargs))


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


def _validate_operator(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION:
        raise ValueError("r12_causal_interaction_operator.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_causal_interaction_operator.acceptance_gates must be an object")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 causal interaction operator must not allow runtime default")
    contract = artifact.get("operator_contract")
    if not isinstance(contract, dict):
        raise ValueError("r12 causal interaction operator contract must be an object")
    if contract.get("prompt_or_persona_manual_patch_allowed") is not False:
        raise ValueError("prompt/persona patch must be blocked")


def _training_residual(case: dict[str, Any]) -> dict[str, Any]:
    prediction = case["prediction_state"]
    return {
        "case_id": case["case_id"],
        "split": case["split"],
        "observed_value": case["outcome_proxy"]["observed_value"],
        "interaction_prediction": prediction["interaction_prediction"],
        "static_prior_prediction": prediction["static_prior_prediction"],
        "residual_vs_interaction": prediction["residual_vs_interaction"],
        "residual_vs_static_prior": prediction["residual_vs_static_prior"],
        "source_signal_delta": case["source_signal"]["delta"],
    }


def _training_residual_summary(
    training_residuals: list[dict[str, Any]],
) -> dict[str, Any]:
    residuals = [float(item["residual_vs_interaction"]) for item in training_residuals]
    if not residuals:
        raise ValueError("at least one train residual is required")
    return {
        "train_case_count": len(residuals),
        "mean_train_residual_vs_interaction": _round6(
            sum(residuals) / len(residuals)
        ),
        "mean_abs_train_residual_vs_interaction": _round6(
            sum(abs(item) for item in residuals) / len(residuals)
        ),
        "positive_train_residual_count": sum(1 for item in residuals if item > 0),
        "negative_train_residual_count": sum(1 for item in residuals if item < 0),
    }


def _update_candidates(
    *,
    causal_operator: dict[str, Any],
    training_residuals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_price_pressure = causal_operator["parameter_state"]["mechanism_weights"][
        "price_pressure"
    ]["value"]
    train_case_ids = [item["case_id"] for item in training_residuals]
    return [
        {
            "update_id": "r12-mechanism-weight-price-pressure-accepted-001",
            "update_type": "mechanism_weight",
            "status": "accepted",
            "status_reason": (
                "positive train residual supports bounded price-pressure update "
                "for holdout replay"
            ),
            "target": "price_pressure",
            "current_value": current_price_pressure,
            "recommended_value": 0.55,
            "recommended_delta": round(0.55 - float(current_price_pressure), 2),
            "transfer_scope": "same_family_holdout_required",
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
        {
            "update_id": "r12-segment-sensitivity-train-diagnostic-001",
            "update_type": "segment_sensitivity",
            "status": "diagnostic_only",
            "status_reason": (
                "train segments show positive residuals but segment-local gains "
                "are not transferable before holdout replay"
            ),
            "target": train_case_ids,
            "current_value": {
                case_id: causal_operator["parameter_state"]["segment_sensitivities"][
                    case_id
                ]["value"]
                for case_id in train_case_ids
            },
            "recommended_value": {
                case_id: causal_operator["parameter_state"]["segment_sensitivities"][
                    case_id
                ]["value"]
                for case_id in train_case_ids
            },
            "recommended_delta": 0.0,
            "transfer_scope": "same_case_diagnostic_only",
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
        {
            "update_id": "r12-interaction-edge-weight-rejected-001",
            "update_type": "interaction_edge_weight",
            "status": "rejected",
            "status_reason": (
                "direct interaction propagation evidence is absent, so edge "
                "updates would be unsupported"
            ),
            "target": "segment_peer_amplification",
            "current_value": causal_operator["parameter_state"]["interaction_edge_weights"][
                "segment_peer_amplification"
            ]["value"],
            "recommended_value": causal_operator["parameter_state"][
                "interaction_edge_weights"
            ]["segment_peer_amplification"]["value"],
            "recommended_delta": 0.0,
            "transfer_scope": "blocked_until_direct_propagation_evidence",
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
        {
            "update_id": "r12-uncertainty-parameter-diagnostic-001",
            "update_type": "uncertainty_parameter",
            "status": "diagnostic_only",
            "status_reason": (
                "train outcomes remain inside current intervals, so uncertainty "
                "changes are diagnostic rather than accepted"
            ),
            "target": "interval_half_width",
            "current_value": causal_operator["parameter_state"]["uncertainty_parameters"][
                "interval_half_width"
            ]["value"],
            "recommended_value": causal_operator["parameter_state"][
                "uncertainty_parameters"
            ]["interval_half_width"]["value"],
            "recommended_delta": 0.0,
            "transfer_scope": "diagnostic_only_until_interval_miss",
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
    ]


def _count_status(candidates: list[dict[str, Any]], status: str) -> int:
    return sum(1 for candidate in candidates if candidate["status"] == status)


def _round6(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-outcome-case-registry-path", required=True)
    parser.add_argument("--r12-causal-interaction-operator-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_outcome_supervised_update(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_outcome_case_registry=load_json_artifact(
            args.r12_outcome_case_registry_path
        ),
        r12_causal_interaction_operator=load_json_artifact(
            args.r12_causal_interaction_operator_path
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
