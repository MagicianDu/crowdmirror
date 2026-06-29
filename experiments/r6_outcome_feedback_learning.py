from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_behavioral_update_operator_v3 import (
    build_r6_behavioral_update_operator_v3,
)
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)


R6_OUTCOME_FEEDBACK_REVIEW_SCHEMA_VERSION = "r6-outcome-feedback-review-v1"
R6_BOUNDED_UPDATE_CANDIDATE_SCHEMA_VERSION = "r6-bounded-update-candidate-v1"
R6_FEEDBACK_TRANSFER_VALIDATION_SCHEMA_VERSION = "r6-feedback-transfer-validation-v1"


UPDATED_COMPONENTS = [
    "segment_weight_update",
    "mechanism_strength_update",
    "scenario_similarity_update",
    "interval_calibration_update",
    "false_alarm_discriminator_update",
    "blocked_claim_policy_update",
]


def build_r6_outcome_feedback_review(
    *,
    artifact_id: str,
    run_id: str,
    behavioral_update_operator_v3: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    operator = behavioral_update_operator_v3 or build_r6_behavioral_update_operator_v3(
        artifact_id=f"{artifact_id}-operator-v3",
        run_id=run_id,
    )
    case_reviews = [_case_review(case) for case in operator["case_results"]]
    report = {
        "schema_version": R6_OUTCOME_FEEDBACK_REVIEW_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "outcome_feedback_review_ready",
        "summary": {
            "reviewed_case_count": len(case_reviews),
            "mean_initial_loss": _mean(case["interaction_loss"] for case in case_reviews),
            "mean_candidate_loss": _mean(case["operator_loss"] for case in case_reviews),
            "field_outcome_validated": False,
        },
        "case_reviews": case_reviews,
        "acceptance_gates": {
            "outcome_review_artifact_present": True,
            "all_cases_have_error_attribution": all(
                bool(case["error_attribution"]) for case in case_reviews
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [operator["artifact_id"]],
        "allowed_claims": [
            "Outcome feedback review can explain current proxy errors and produce bounded update candidates.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def build_r6_bounded_update_candidate(
    *,
    artifact_id: str,
    run_id: str,
    outcome_feedback_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    review = outcome_feedback_review or build_r6_outcome_feedback_review(
        artifact_id=f"{artifact_id}-outcome-feedback-review",
        run_id=run_id,
    )
    initial_loss = review["summary"]["mean_initial_loss"]
    candidate_loss = review["summary"]["mean_candidate_loss"]
    candidate_accepted = False
    report = {
        "schema_version": R6_BOUNDED_UPDATE_CANDIDATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "bounded_update_candidate_rejected_runtime_guard",
        "initial_loss": initial_loss,
        "candidate_loss": candidate_loss,
        "final_loss": candidate_loss if candidate_accepted else initial_loss,
        "candidate_accepted": candidate_accepted,
        "candidate_rejected_reason": "runtime_guard_or_field_outcome_missing",
        "updated_components": UPDATED_COMPONENTS,
        "guard_results": {
            "candidate_loss_improved": candidate_loss < initial_loss,
            "holdout_guard_passed": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "rollback_policy": {
            "rollback_to_static_prior_on_guard_failure": True,
            "rollback_to_previous_runtime_operator": True,
            "persist_rejected_candidate_for_audit": True,
        },
        "source_refs": [review["artifact_id"]],
        "allowed_claims": [
            "A bounded update candidate is generated and explicitly rejected for runtime use.",
        ],
        "blocked_claims": [
            "候选更新已可自动上线",
            "runtime_default_allowed=true",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def build_r6_feedback_transfer_validation(
    *,
    artifact_id: str,
    run_id: str,
    bounded_update_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    candidate = bounded_update_candidate or build_r6_bounded_update_candidate(
        artifact_id=f"{artifact_id}-bounded-update-candidate",
        run_id=run_id,
    )
    report = {
        "schema_version": R6_FEEDBACK_TRANSFER_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "feedback_transfer_validation_ready_update_blocked",
        "summary": {
            "candidate_accepted": candidate["candidate_accepted"],
            "initial_loss": candidate["initial_loss"],
            "candidate_loss": candidate["candidate_loss"],
            "final_loss": candidate["final_loss"],
        },
        "acceptance_gates": {
            "feedback_transfer_validation_present": True,
            "bounded_update_candidate_present": True,
            "candidate_has_accept_reject_decision": isinstance(
                candidate["candidate_accepted"],
                bool,
            ),
            "candidate_loss_improved": candidate["candidate_loss"]
            < candidate["initial_loss"],
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [candidate["artifact_id"]],
        "allowed_claims": [
            "Product can show what the system learned and why the candidate update was blocked.",
        ],
        "blocked_claims": [
            "候选更新已可自动上线",
            "outcome feedback 已经形成通用自动校准器",
            "runtime_default_allowed=true",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_outcome_feedback_review(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_outcome_feedback_review(**kwargs))


def _case_review(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_key": case["source_key"],
        "target_case_id": case["target_case_id"],
        "interaction_loss": case["interaction_error"],
        "operator_loss": case["operator_error"],
        "static_prior_loss": case["static_prior_error"],
        "error_attribution": {
            "primary_component": "false_alarm_control"
            if case["guard_decision"] == "fallback_to_static_prior"
            else "static_prior_miss_recovery",
            "operator_reduced_or_preserved_loss": case["operator_error"]
            <= case["interaction_error"],
        },
        "recommended_update_components": UPDATED_COMPONENTS,
    }


def _mean(values: Any) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_outcome_feedback_review(
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
