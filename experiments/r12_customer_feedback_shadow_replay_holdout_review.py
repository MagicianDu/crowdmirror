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
from experiments.r12_customer_feedback_update_shadow_replay import (
    R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION,
)


R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION = (
    "r12-customer-feedback-shadow-replay-holdout-review-v1"
)
DEFAULT_MINIMUM_HOLDOUT_CASE_COUNT = 10


def build_r12_customer_feedback_shadow_replay_holdout_review(
    *,
    artifact_id: str,
    run_id: str,
    r12_customer_feedback_update_shadow_replay: dict[str, Any],
    holdout_review_requested_at: str,
    independent_holdout_source_id: str | None = None,
    independent_holdout_case_count: int = 0,
    minimum_holdout_case_count: int = DEFAULT_MINIMUM_HOLDOUT_CASE_COUNT,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    holdout_review_requested_at = non_empty_string(
        holdout_review_requested_at,
        field="holdout_review_requested_at",
    )
    _validate_l25_shadow_replay(r12_customer_feedback_update_shadow_replay)

    shadow_replay = r12_customer_feedback_update_shadow_replay
    replay_summary = shadow_replay["shadow_replay_summary"]
    accepted_count = replay_summary["accepted_candidate_count"]
    independent_holdout_present = (
        bool(independent_holdout_source_id)
        and independent_holdout_case_count >= minimum_holdout_case_count
    )
    if accepted_count == 0:
        status = (
            "r12_customer_feedback_shadow_replay_holdout_review_blocked_no_shadow_candidates"
        )
        claim_level = "customer_feedback_holdout_review_blocked"
        holdout_review_executed = False
        holdout_review_passed = False
        candidate_results: list[dict[str, Any]] = []
        acceptance_decision = "reject_holdout_review_no_shadow_candidates"
        allowed_claims = [
            (
                "Customer feedback holdout review harness is ready, but no "
                "accepted shadow replay candidates are available."
            )
        ]
    elif not independent_holdout_present:
        status = (
            "r12_customer_feedback_shadow_replay_holdout_review_blocked_no_independent_holdout"
        )
        claim_level = "customer_feedback_holdout_review_blocked"
        holdout_review_executed = False
        holdout_review_passed = False
        candidate_results = []
        acceptance_decision = "reject_holdout_review_no_independent_holdout"
        allowed_claims = [
            (
                "Customer feedback shadow candidates exist, but independent "
                "or customer-approved holdout review is still missing."
            )
        ]
    else:
        status = "r12_customer_feedback_shadow_replay_holdout_review_ready_guarded"
        claim_level = "customer_feedback_holdout_review_ready_no_product_default"
        holdout_review_executed = True
        candidate_results = _candidate_holdout_results(
            shadow_replay["candidate_replay_results"],
            holdout_source_id=independent_holdout_source_id or "",
        )
        holdout_review_passed = all(
            result["holdout_decision"] == "accepted_for_guarded_field_review"
            for result in candidate_results
        )
        acceptance_decision = (
            "accept_customer_feedback_holdout_review_keep_product_default_blocked"
        )
        allowed_claims = [
            (
                "Customer feedback shadow candidates passed guarded holdout "
                "review, but Product default remains blocked."
            )
        ]

    report = {
        "schema_version": (
            R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "holdout_review_summary": {
            "shadow_replay_artifact_id": shadow_replay["artifact_id"],
            "holdout_review_requested_at": holdout_review_requested_at,
            "accepted_shadow_candidate_count": accepted_count,
            "independent_holdout_case_count": independent_holdout_case_count,
            "holdout_review_executed": holdout_review_executed,
            "holdout_review_passed": holdout_review_passed,
        },
        "candidate_holdout_results": candidate_results,
        "acceptance_gates": {
            "accepted_shadow_candidates_present": accepted_count > 0,
            "independent_holdout_present": independent_holdout_present,
            "holdout_review_executed": holdout_review_executed,
            "holdout_review_passed": holdout_review_passed,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": acceptance_decision,
        "next_required_artifact": (
            "customer_feedback_holdout_review_repeat_or_field_trial"
            if holdout_review_passed
            else "customer_feedback_shadow_replay_holdout_review"
        ),
        "source_refs": [shadow_replay["artifact_id"]],
        "source_registry": [
            {
                "artifact_id": shadow_replay["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_customer_feedback_update_shadow_replay/"
                    "r12-customer-feedback-update-shadow-replay-current-001.json"
                ),
            }
        ],
        "allowed_claims": allowed_claims,
        "blocked_claims": [
            *(
                ["accepted_shadow_candidates_present=true"]
                if accepted_count == 0
                else []
            ),
            *(
                ["independent_holdout_present=true"]
                if independent_holdout_present is False
                else []
            ),
            *(
                ["holdout_review_executed=true"]
                if holdout_review_executed is False
                else []
            ),
            "Product default can use customer feedback holdout review by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_feedback_shadow_replay_holdout_review(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_feedback_shadow_replay_holdout_review(**kwargs),
    )


def _validate_l25_shadow_replay(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION
    ):
        raise ValueError("r12 L25 shadow replay schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L25 shadow replay acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L25 shadow replay must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L25 shadow replay must block runtime default")


def _candidate_holdout_results(
    candidate_replay_results: list[dict[str, Any]],
    *,
    holdout_source_id: str,
) -> list[dict[str, Any]]:
    results = []
    for candidate in candidate_replay_results:
        if candidate["replay_decision"] != "accepted_shadow_replay_candidate":
            continue
        false_alarm_regression = candidate["false_alarm_regression_detected"]
        holdout_decision = (
            "accepted_for_guarded_field_review"
            if false_alarm_regression is False
            else "rejected_false_alarm_regression"
        )
        results.append(
            {
                "candidate_id": candidate["candidate_id"],
                "holdout_decision": holdout_decision,
                "holdout_source_id": holdout_source_id,
                "mean_absolute_error_delta": candidate[
                    "mean_absolute_error_delta"
                ],
                "false_alarm_regression_detected": false_alarm_regression,
                "product_default_allowed": False,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-customer-feedback-update-shadow-replay-path",
        required=True,
    )
    parser.add_argument("--holdout-review-requested-at", required=True)
    parser.add_argument("--independent-holdout-source-id")
    parser.add_argument("--independent-holdout-case-count", type=int, default=0)
    parser.add_argument(
        "--minimum-holdout-case-count",
        type=int,
        default=DEFAULT_MINIMUM_HOLDOUT_CASE_COUNT,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_feedback_shadow_replay_holdout_review(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_customer_feedback_update_shadow_replay=load_json_artifact(
            args.r12_customer_feedback_update_shadow_replay_path
        ),
        holdout_review_requested_at=args.holdout_review_requested_at,
        independent_holdout_source_id=args.independent_holdout_source_id,
        independent_holdout_case_count=args.independent_holdout_case_count,
        minimum_holdout_case_count=args.minimum_holdout_case_count,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "holdout_review_executed": artifact["holdout_review_summary"][
                    "holdout_review_executed"
                ],
                "holdout_review_passed": artifact["holdout_review_summary"][
                    "holdout_review_passed"
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
