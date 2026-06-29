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
from experiments.r12_customer_field_slice_revalidation import (
    R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION,
)


R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION = (
    "r12-customer-field-outcome-feedback-update-v1"
)


def build_r12_customer_field_outcome_feedback_update(
    *,
    artifact_id: str,
    run_id: str,
    r12_customer_field_slice_revalidation: dict[str, Any],
    feedback_generated_at: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    feedback_generated_at = non_empty_string(
        feedback_generated_at,
        field="feedback_generated_at",
    )
    _validate_l23_revalidation(r12_customer_field_slice_revalidation)

    revalidation = r12_customer_field_slice_revalidation
    gates = revalidation["acceptance_gates"]
    metrics = revalidation["metric_results"]
    field_outcome_validated = gates["field_outcome_validated"] is True
    metrics_consumed = gates["metrics_computed"] is True and field_outcome_validated
    if metrics_consumed:
        candidate_updates = _candidate_updates(metrics)
        status = (
            "r12_customer_field_outcome_feedback_update_candidates_ready_guarded"
        )
        claim_level = (
            "customer_field_feedback_update_candidates_no_product_default"
        )
        acceptance_decision = (
            "accept_customer_feedback_update_candidates_for_shadow_review"
        )
        allowed_claims = [
            (
                "Customer field outcome feedback produced bounded update "
                "candidates for shadow review."
            ),
            (
                "Feedback update candidates are structured parameter updates, "
                "not direct prompt/persona patches and not Product defaults."
            ),
        ]
    else:
        candidate_updates = []
        status = (
            "r12_customer_field_outcome_feedback_update_blocked_no_field_validation"
        )
        claim_level = "customer_field_feedback_update_blocked"
        acceptance_decision = "reject_feedback_update_no_validated_field_outcome"
        allowed_claims = [
            (
                "Customer field outcome feedback update harness is ready, but "
                "no validated field outcome is available."
            )
        ]

    report = {
        "schema_version": R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "feedback_summary": {
            "revalidation_artifact_id": revalidation["artifact_id"],
            "feedback_generated_at": feedback_generated_at,
            "metrics_consumed": metrics_consumed,
            "field_outcome_validated": field_outcome_validated,
            "candidate_count": len(candidate_updates),
        },
        "metric_inputs": _metric_inputs(metrics) if metrics_consumed else {},
        "candidate_updates": candidate_updates,
        "acceptance_gates": {
            "field_outcome_validated": field_outcome_validated,
            "metrics_consumed": metrics_consumed,
            "candidate_updates_generated": bool(candidate_updates),
            "prompt_or_persona_manual_patch_allowed": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": acceptance_decision,
        "next_required_artifact": (
            "r12_customer_feedback_update_shadow_replay"
            if candidate_updates
            else "validated_customer_field_slice_revalidation"
        ),
        "source_refs": [revalidation["artifact_id"]],
        "source_registry": [
            {
                "artifact_id": revalidation["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_slice_revalidation/"
                    "r12-customer-field-slice-revalidation-current-001.json"
                ),
            }
        ],
        "allowed_claims": allowed_claims,
        "blocked_claims": [
            *(
                ["metrics_consumed=true"]
                if metrics_consumed is False
                else []
            ),
            *(
                ["candidate_updates_generated=true"]
                if not candidate_updates
                else []
            ),
            "manual prompt/persona patch from customer feedback",
            "Product default can use customer feedback update by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_field_outcome_feedback_update(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_field_outcome_feedback_update(**kwargs),
    )


def _validate_l23_revalidation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L23 revalidation schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L23 revalidation acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L23 revalidation must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L23 revalidation must block runtime default")


def _candidate_updates(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    mean_signed_error = float(metrics["mean_signed_error"])
    risk_ranking_quality = float(metrics["risk_ranking_quality"])
    if mean_signed_error < 0:
        pressure_update = {
            "candidate_id": "field-feedback-risk-pressure-increase-001",
            "update_target": "risk_pressure_multiplier",
            "update_direction": "increase",
            "rationale": (
                "Observed outcomes are higher than predictions; increase "
                "risk-pressure response in shadow review."
            ),
            "evidence_metric": "mean_signed_error",
            "evidence_value": _round(mean_signed_error),
            "review_status": "shadow_review_required",
            "product_default_allowed": False,
        }
    elif mean_signed_error > 0:
        pressure_update = {
            "candidate_id": "field-feedback-risk-pressure-decrease-001",
            "update_target": "risk_pressure_multiplier",
            "update_direction": "decrease",
            "rationale": (
                "Observed outcomes are lower than predictions; decrease "
                "risk-pressure response in shadow review."
            ),
            "evidence_metric": "mean_signed_error",
            "evidence_value": _round(mean_signed_error),
            "review_status": "shadow_review_required",
            "product_default_allowed": False,
        }
    else:
        pressure_update = {
            "candidate_id": "field-feedback-risk-pressure-preserve-001",
            "update_target": "risk_pressure_multiplier",
            "update_direction": "preserve",
            "rationale": (
                "Observed outcomes match predictions on average; preserve "
                "risk-pressure level in shadow review."
            ),
            "evidence_metric": "mean_signed_error",
            "evidence_value": _round(mean_signed_error),
            "review_status": "shadow_review_required",
            "product_default_allowed": False,
        }
    ranking_update = {
        "candidate_id": "field-feedback-ranking-preserve-001",
        "update_target": "risk_ranking_operator",
        "update_direction": "preserve",
        "rationale": (
            "Field ranking quality passed threshold; preserve ranking "
            "operator and focus calibration update on level bias."
        ),
        "evidence_metric": "risk_ranking_quality",
        "evidence_value": _round(risk_ranking_quality),
        "review_status": "shadow_review_required",
        "product_default_allowed": False,
    }
    return [pressure_update, ranking_update]


def _metric_inputs(metrics: dict[str, Any]) -> dict[str, float]:
    return {
        "mean_absolute_error": _round(float(metrics["mean_absolute_error"])),
        "mean_signed_error": _round(float(metrics["mean_signed_error"])),
        "risk_ranking_quality": _round(float(metrics["risk_ranking_quality"])),
        "top_quintile_overlap": _round(float(metrics["top_quintile_overlap"])),
    }


def _round(value: float) -> float:
    return round(value, 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-customer-field-slice-revalidation-path",
        required=True,
    )
    parser.add_argument("--feedback-generated-at", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_field_outcome_feedback_update(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_customer_field_slice_revalidation=load_json_artifact(
            args.r12_customer_field_slice_revalidation_path
        ),
        feedback_generated_at=args.feedback_generated_at,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "candidate_count": artifact["feedback_summary"][
                    "candidate_count"
                ],
                "metrics_consumed": artifact["acceptance_gates"][
                    "metrics_consumed"
                ],
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
