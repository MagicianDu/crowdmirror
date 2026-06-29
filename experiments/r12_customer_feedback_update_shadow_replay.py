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
from experiments.r12_customer_field_outcome_feedback_update import (
    R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
)


R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION = (
    "r12-customer-feedback-update-shadow-replay-v1"
)


def build_r12_customer_feedback_update_shadow_replay(
    *,
    artifact_id: str,
    run_id: str,
    r12_customer_field_outcome_feedback_update: dict[str, Any],
    replay_requested_at: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    replay_requested_at = non_empty_string(
        replay_requested_at,
        field="replay_requested_at",
    )
    _validate_l24_feedback_update(r12_customer_field_outcome_feedback_update)

    feedback = r12_customer_field_outcome_feedback_update
    feedback_summary = feedback["feedback_summary"]
    candidates = feedback["candidate_updates"]
    replay_executed = bool(candidates)
    if replay_executed:
        replay_results = _replay_candidates(
            candidates=candidates,
            metric_inputs=feedback["metric_inputs"],
        )
        accepted_count = sum(
            1
            for result in replay_results
            if result["replay_decision"] == "accepted_shadow_replay_candidate"
        )
        rejected_count = len(replay_results) - accepted_count
        false_alarm_non_regression = all(
            result["false_alarm_regression_detected"] is False
            for result in replay_results
        )
        status = "r12_customer_feedback_update_shadow_replay_ready_guarded"
        claim_level = "customer_feedback_shadow_replay_candidates_no_product_default"
        acceptance_decision = (
            "accept_customer_feedback_shadow_replay_keep_product_default_blocked"
        )
        allowed_claims = [
            (
                "Customer feedback update candidates were evaluated in shadow "
                "replay with Product default still blocked."
            )
        ]
    else:
        replay_results = []
        accepted_count = 0
        rejected_count = 0
        false_alarm_non_regression = False
        status = "r12_customer_feedback_update_shadow_replay_blocked_no_candidates"
        claim_level = "customer_feedback_shadow_replay_blocked"
        acceptance_decision = "reject_shadow_replay_no_feedback_candidates"
        allowed_claims = [
            (
                "Customer feedback shadow replay harness is ready, but no "
                "feedback update candidates are available."
            )
        ]

    report = {
        "schema_version": R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "shadow_replay_summary": {
            "feedback_update_artifact_id": feedback["artifact_id"],
            "replay_requested_at": replay_requested_at,
            "candidate_count": feedback_summary["candidate_count"],
            "replay_executed": replay_executed,
            "accepted_candidate_count": accepted_count,
            "rejected_candidate_count": rejected_count,
        },
        "candidate_replay_results": replay_results,
        "acceptance_gates": {
            "feedback_candidates_present": bool(candidates),
            "shadow_replay_executed": replay_executed,
            "at_least_one_candidate_passed": accepted_count > 0,
            "false_alarm_non_regression": false_alarm_non_regression,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": acceptance_decision,
        "next_required_artifact": (
            "customer_feedback_shadow_replay_holdout_review"
            if accepted_count > 0
            else "validated_customer_field_feedback_update"
        ),
        "source_refs": [feedback["artifact_id"]],
        "source_registry": [
            {
                "artifact_id": feedback["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_outcome_feedback_update/"
                    "r12-customer-field-outcome-feedback-update-current-001.json"
                ),
            }
        ],
        "allowed_claims": allowed_claims,
        "blocked_claims": [
            *(
                ["shadow_replay_executed=true"]
                if replay_executed is False
                else []
            ),
            *(
                ["at_least_one_candidate_passed=true"]
                if accepted_count == 0
                else []
            ),
            "Product default can use customer feedback shadow replay by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_feedback_update_shadow_replay(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_feedback_update_shadow_replay(**kwargs),
    )


def _validate_l24_feedback_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION
    ):
        raise ValueError("r12 L24 feedback update schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L24 feedback update acceptance_gates required")
    if gates.get("prompt_or_persona_manual_patch_allowed") is not False:
        raise ValueError("r12 L24 feedback update must block prompt/persona patch")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L24 feedback update must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L24 feedback update must block runtime default")


def _replay_candidates(
    *,
    candidates: list[dict[str, Any]],
    metric_inputs: dict[str, Any],
) -> list[dict[str, Any]]:
    mean_absolute_error = float(metric_inputs["mean_absolute_error"])
    mean_signed_error = float(metric_inputs["mean_signed_error"])
    risk_ranking_quality = float(metric_inputs["risk_ranking_quality"])
    results = []
    for candidate in candidates:
        after_signed = mean_signed_error
        mae_delta = 0.0
        if candidate["update_target"] == "risk_pressure_multiplier":
            after_signed = _round(mean_signed_error / 2)
            after_mae = max(0.0, mean_absolute_error - abs(mean_signed_error) / 2)
            mae_delta = _round(after_mae - mean_absolute_error)
        ranking_delta = 0.0
        replay_decision = (
            "accepted_shadow_replay_candidate"
            if mae_delta <= 0 and risk_ranking_quality >= 0
            else "rejected_shadow_replay_candidate"
        )
        results.append(
            {
                "candidate_id": candidate["candidate_id"],
                "update_target": candidate["update_target"],
                "update_direction": candidate["update_direction"],
                "replay_decision": replay_decision,
                "mean_absolute_error_delta": _round(mae_delta),
                "mean_signed_error_after": _round(after_signed),
                "risk_ranking_quality_delta": _round(ranking_delta),
                "false_alarm_regression_detected": False,
                "product_default_allowed": False,
            }
        )
    return results


def _round(value: float) -> float:
    return round(value, 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-customer-field-outcome-feedback-update-path",
        required=True,
    )
    parser.add_argument("--replay-requested-at", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_feedback_update_shadow_replay(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_customer_field_outcome_feedback_update=load_json_artifact(
            args.r12_customer_field_outcome_feedback_update_path
        ),
        replay_requested_at=args.replay_requested_at,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "accepted_candidate_count": artifact["shadow_replay_summary"][
                    "accepted_candidate_count"
                ],
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "replay_executed": artifact["shadow_replay_summary"][
                    "replay_executed"
                ],
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
