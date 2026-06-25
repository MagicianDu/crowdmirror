from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_UPDATE_STATUSES,
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r11_external_holdout_validation import (
    R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
)
from experiments.r11_product_shadow_trial import R11_PRODUCT_SHADOW_TRIAL_SCHEMA_VERSION


R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION = "r11-outcome-feedback-update-v1"
R11_OUTCOME_FEEDBACK_UPDATE_CLAIM_BOUNDARY = (
    "R11 outcome feedback update artifact. It converts R11 shadow-trial "
    "outcome feedback into bounded update candidates for mechanism weights, "
    "segment sensitivity, propagation edges, and interval uncertainty. It does "
    "not permit prompt/persona manual patches, field-validation claims, or "
    "runtime default updates."
)
DEFAULT_FEEDBACK_PACKET = {
    "feedback_id": "r11-shadow-feedback-public-proxy-replay-current-001",
    "measurement_window": "hps_public_proxy_replay",
    "source_level": "public_proxy_replay",
    "case_measurements": [
        {
            "case_id": "hps_REGION_2",
            "observed_outcome_proxy": 0.538224,
            "evidence_note": "public proxy replay indicates stronger high-risk reaction",
        },
        {
            "case_id": "hps_METRO_STATUS_2",
            "observed_outcome_proxy": 0.593338,
            "evidence_note": "public proxy replay indicates strongest metro risk",
        },
        {
            "case_id": "hps_REGION_1",
            "observed_outcome_proxy": 0.430869,
            "evidence_note": "public proxy replay indicates lower low-risk reaction",
        },
    ],
}


def build_r11_outcome_feedback_update(
    *,
    artifact_id: str,
    run_id: str,
    r11_product_shadow_trial: dict[str, Any],
    r11_external_holdout_validation: dict[str, Any],
    observed_feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_shadow_trial(r11_product_shadow_trial)
    _validate_holdout(r11_external_holdout_validation)
    feedback = _normalize_feedback(observed_feedback)
    residuals = _case_residuals(
        feedback=feedback,
        holdout_cases=r11_external_holdout_validation["external_holdout_cases"],
    )
    residual_summary = _residual_summary(residuals)
    attribution = _error_attribution(residual_summary)
    candidates = _update_candidates(
        residuals=residuals,
        attribution=attribution,
        source_level=feedback["source_level"],
    )
    update_gate = _update_gate(candidates)
    report = {
        "schema_version": R11_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r11_outcome_feedback_update_ready_guarded",
        "claim_level": "bounded_update_candidate_only",
        "claim_boundary": R11_OUTCOME_FEEDBACK_UPDATE_CLAIM_BOUNDARY,
        "feedback_contract": {
            "source_backed_only": True,
            "feedback_source_level": feedback["source_level"],
            "updates_are_bounded_candidates": True,
            "prompt_or_persona_manual_patch_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "observed_feedback": feedback,
        "case_residuals": residuals,
        "residual_summary": residual_summary,
        "error_attribution": attribution,
        "update_candidates": candidates,
        "update_gate": update_gate,
        "source_refs": [
            r11_product_shadow_trial["artifact_id"],
            r11_external_holdout_validation["artifact_id"],
            feedback["feedback_id"],
        ],
        "allowed_claims": [
            "R11 can generate bounded update candidates from shadow-trial feedback.",
            "Update candidates are auditable and separated from runtime default.",
        ],
        "blocked_claims": [
            "R11 runtime default update",
            "R11 field validated",
            "R11 supports Product core method by default",
            "prompt/persona manual patch is an automatic calibration method",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r11_outcome_feedback_update(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r11_outcome_feedback_update(**kwargs))


def _validate_shadow_trial(shadow: dict[str, Any]) -> None:
    if shadow.get("schema_version") != R11_PRODUCT_SHADOW_TRIAL_SCHEMA_VERSION:
        raise ValueError(
            "r11_product_shadow_trial.schema_version must be "
            f"{R11_PRODUCT_SHADOW_TRIAL_SCHEMA_VERSION}"
        )
    contract = shadow.get("trial_contract")
    if not isinstance(contract, dict):
        raise ValueError("r11_product_shadow_trial.trial_contract must be an object")
    if contract.get("shadow_only") is not True:
        raise ValueError("r11_product_shadow_trial must be shadow only")
    if contract.get("r11_can_override_primary_decision") is not False:
        raise ValueError("r11_product_shadow_trial cannot override primary decision")
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError("r11_product_shadow_trial must not allow runtime default")


def _validate_holdout(holdout: dict[str, Any]) -> None:
    if holdout.get("schema_version") != R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION:
        raise ValueError(
            "r11_external_holdout_validation.schema_version must be "
            f"{R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION}"
        )
    gates = holdout.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r11_external_holdout_validation.acceptance_gates must be an object")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r11 external holdout must not allow runtime default")


def _normalize_feedback(observed_feedback: dict[str, Any] | None) -> dict[str, Any]:
    feedback = observed_feedback or DEFAULT_FEEDBACK_PACKET
    if not isinstance(feedback, dict):
        raise ValueError("observed_feedback must be an object")
    case_measurements = feedback.get("case_measurements")
    if not isinstance(case_measurements, list) or not case_measurements:
        raise ValueError("observed_feedback.case_measurements must be a non-empty list")
    normalized_cases = []
    for index, item in enumerate(case_measurements):
        if not isinstance(item, dict):
            raise ValueError(f"observed_feedback.case_measurements[{index}] must be an object")
        normalized_cases.append(
            {
                "case_id": non_empty_string(
                    item.get("case_id"),
                    field=f"observed_feedback.case_measurements[{index}].case_id",
                ),
                "observed_outcome_proxy": round(
                    float(item["observed_outcome_proxy"]),
                    6,
                ),
                "evidence_note": non_empty_string(
                    item.get("evidence_note"),
                    field=f"observed_feedback.case_measurements[{index}].evidence_note",
                ),
            }
        )
    return {
        "feedback_id": non_empty_string(
            feedback.get("feedback_id"),
            field="observed_feedback.feedback_id",
        ),
        "measurement_window": non_empty_string(
            feedback.get("measurement_window"),
            field="observed_feedback.measurement_window",
        ),
        "source_level": non_empty_string(
            feedback.get("source_level"),
            field="observed_feedback.source_level",
        ),
        "case_measurements": normalized_cases,
    }


def _case_residuals(
    *,
    feedback: dict[str, Any],
    holdout_cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    holdout_by_case_id = {case["case_id"]: case for case in holdout_cases}
    residuals = []
    for measurement in feedback["case_measurements"]:
        case_id = measurement["case_id"]
        if case_id not in holdout_by_case_id:
            raise ValueError(f"feedback case not present in holdout: {case_id}")
        case = holdout_by_case_id[case_id]
        observed = float(measurement["observed_outcome_proxy"])
        prediction = float(case["r11_prediction"])
        interval = case["risk_interval"]
        residual = round(observed - prediction, 6)
        residuals.append(
            {
                "case_id": case_id,
                "segment_column": case["segment_column"],
                "segment_value": case["segment_value"],
                "r11_prediction": round(prediction, 6),
                "observed_outcome_proxy": round(observed, 6),
                "signed_residual": residual,
                "absolute_residual": round(abs(residual), 6),
                "interval_contains_feedback": interval["p10"] <= observed <= interval["p90"],
                "evidence_note": measurement["evidence_note"],
            }
        )
    return residuals


def _residual_summary(residuals: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(residuals)
    signed = [case["signed_residual"] for case in residuals]
    absolute = [case["absolute_residual"] for case in residuals]
    return {
        "feedback_case_count": count,
        "mean_signed_residual": round(sum(signed) / count, 3),
        "mean_absolute_residual": round(sum(absolute) / count, 3),
        "positive_residual_count": sum(1 for value in signed if value > 0),
        "negative_residual_count": sum(1 for value in signed if value < 0),
        "interval_miss_count": sum(
            1 for case in residuals if not case["interval_contains_feedback"]
        ),
    }


def _error_attribution(summary: dict[str, Any]) -> dict[str, Any]:
    segment_specific = (
        summary["positive_residual_count"] >= 2
        and summary["negative_residual_count"] >= 1
    )
    return {
        "primary_error_mode": (
            "segment_specific_under_reaction"
            if segment_specific
            else "global_feedback_residual_review"
        ),
        "mechanism_weight_update_needed": summary["mean_signed_residual"] > 0.015,
        "segment_sensitivity_update_needed": segment_specific,
        "propagation_edge_update_supported": False,
        "interval_uncertainty_update_needed": summary["interval_miss_count"] > 0,
    }


def _update_candidates(
    *,
    residuals: list[dict[str, Any]],
    attribution: dict[str, Any],
    source_level: str,
) -> list[dict[str, Any]]:
    largest = max(residuals, key=lambda item: item["absolute_residual"])
    mechanism_status = (
        "diagnostic_only"
        if attribution["mechanism_weight_update_needed"]
        else "rejected"
    )
    interval_status = (
        "diagnostic_only"
        if not attribution["interval_uncertainty_update_needed"]
        else "accepted"
    )
    candidates = [
        {
            "update_id": "r11-mechanism-weight-diagnostic-001",
            "update_type": "mechanism_weight",
            "status": mechanism_status,
            "status_reason": (
                f"{source_level} residual suggests price-pressure weight review, "
                "but evidence is not sufficient for runtime default"
            ),
            "target": "price_pressure",
            "recommended_delta": 0.02,
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
        {
            "update_id": "r11-segment-sensitivity-shadow-accepted-001",
            "update_type": "segment_sensitivity",
            "status": "accepted",
            "status_reason": "largest residual segment can be replayed in shadow mode only",
            "target": largest["case_id"],
            "recommended_delta": round(largest["absolute_residual"], 2),
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
        {
            "update_id": "r11-propagation-edge-rejected-001",
            "update_type": "propagation_edge",
            "status": "rejected",
            "status_reason": "feedback packet lacks direct interaction propagation evidence",
            "target": "social_amplification_edge",
            "recommended_delta": 0.0,
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
        {
            "update_id": "r11-interval-uncertainty-diagnostic-001",
            "update_type": "interval_uncertainty",
            "status": interval_status,
            "status_reason": (
                "feedback remains inside interval; keep interval review diagnostic"
                if interval_status == "diagnostic_only"
                else "feedback exceeded interval; widen uncertainty in shadow review"
            ),
            "target": "r11_shadow_interval_margin",
            "recommended_delta": 0.0 if interval_status == "diagnostic_only" else 0.05,
            "default_runtime_enabled": False,
            "requires_human_review": True,
        },
    ]
    for candidate in candidates:
        if candidate["status"] not in R6_UPDATE_STATUSES:
            raise ValueError("invalid update candidate status")
    return candidates


def _update_gate(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "candidate_update_generated": True,
        "accepted_shadow_only_count": sum(
            1 for candidate in candidates if candidate["status"] == "accepted"
        ),
        "diagnostic_only_count": sum(
            1 for candidate in candidates if candidate["status"] == "diagnostic_only"
        ),
        "rejected_count": sum(
            1 for candidate in candidates if candidate["status"] == "rejected"
        ),
        "runtime_default_allowed": False,
        "requires_holdout_before_default": True,
        "prompt_or_persona_manual_patch_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r11-product-shadow-trial-path", required=True)
    parser.add_argument("--r11-external-holdout-validation-path", required=True)
    parser.add_argument("--observed-feedback-path", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    feedback = (
        load_json_artifact(args.observed_feedback_path)
        if args.observed_feedback_path
        else None
    )
    output_path = write_r11_outcome_feedback_update(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r11_product_shadow_trial=load_json_artifact(args.r11_product_shadow_trial_path),
        r11_external_holdout_validation=load_json_artifact(
            args.r11_external_holdout_validation_path
        ),
        observed_feedback=feedback,
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
