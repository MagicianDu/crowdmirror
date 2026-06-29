from __future__ import annotations

import argparse
import csv
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
from experiments.r12_customer_feedback_shadow_replay_holdout_review import (
    write_r12_customer_feedback_shadow_replay_holdout_review,
)
from experiments.r12_customer_feedback_update_shadow_replay import (
    write_r12_customer_feedback_update_shadow_replay,
)
from experiments.r12_customer_field_outcome_feedback_update import (
    write_r12_customer_field_outcome_feedback_update,
)
from experiments.r12_customer_field_slice_handoff_package import (
    R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_intake_validation import (
    write_r12_customer_field_slice_intake_validation,
)
from experiments.r12_customer_field_slice_revalidation import (
    write_r12_customer_field_slice_revalidation,
)


R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION = (
    "r12-customer-feedback-loop-operator-rehearsal-v1"
)


def build_r12_customer_feedback_loop_operator_rehearsal(
    *,
    artifact_id: str,
    run_id: str,
    r12_customer_field_slice_handoff_package: dict[str, Any],
    r12_customer_field_slice_handoff_package_path: str | Path,
    rehearsal_started_at: str,
    rehearsal_work_dir: str | Path,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    rehearsal_started_at = non_empty_string(
        rehearsal_started_at,
        field="rehearsal_started_at",
    )
    handoff_path = non_empty_string(
        str(r12_customer_field_slice_handoff_package_path),
        field="r12_customer_field_slice_handoff_package_path",
    )
    _validate_l21_handoff(r12_customer_field_slice_handoff_package)

    handoff = r12_customer_field_slice_handoff_package
    contract = handoff["field_slice_contract"]
    work_dir = Path(rehearsal_work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    sample_slice_path = work_dir / "r12-customer-feedback-loop-rehearsal-sample.csv"
    _write_synthetic_feedback_loop_slice(
        path=sample_slice_path,
        required_fields=contract["required_fields"],
        case_count=contract["minimum_case_count"],
    )

    intake_path = (
        work_dir
        / "r12-customer-field-slice-intake-validation-feedback-loop-rehearsal.json"
    )
    revalidation_path = (
        work_dir
        / "r12-customer-field-slice-revalidation-feedback-loop-rehearsal.json"
    )
    feedback_path = (
        work_dir
        / "r12-customer-field-outcome-feedback-update-feedback-loop-rehearsal.json"
    )
    shadow_replay_path = (
        work_dir
        / "r12-customer-feedback-update-shadow-replay-feedback-loop-rehearsal.json"
    )
    holdout_review_path = (
        work_dir
        / "r12-customer-feedback-shadow-replay-holdout-review-feedback-loop-rehearsal.json"
    )

    write_r12_customer_field_slice_intake_validation(
        output=intake_path,
        artifact_id="r12-customer-field-slice-intake-validation-feedback-loop-rehearsal",
        run_id=f"{run_id}-l22",
        r12_customer_field_slice_handoff_package=handoff,
        intake_checked_at=rehearsal_started_at,
        customer_field_slice_path=sample_slice_path,
    )
    intake = load_json_artifact(intake_path)
    write_r12_customer_field_slice_revalidation(
        output=revalidation_path,
        artifact_id="r12-customer-field-slice-revalidation-feedback-loop-rehearsal",
        run_id=f"{run_id}-l23",
        r12_customer_field_slice_intake_validation=intake,
        revalidation_checked_at=rehearsal_started_at,
    )
    revalidation = load_json_artifact(revalidation_path)
    write_r12_customer_field_outcome_feedback_update(
        output=feedback_path,
        artifact_id="r12-customer-field-outcome-feedback-update-feedback-loop-rehearsal",
        run_id=f"{run_id}-l24",
        r12_customer_field_slice_revalidation=revalidation,
        feedback_generated_at=rehearsal_started_at,
    )
    feedback = load_json_artifact(feedback_path)
    write_r12_customer_feedback_update_shadow_replay(
        output=shadow_replay_path,
        artifact_id="r12-customer-feedback-update-shadow-replay-feedback-loop-rehearsal",
        run_id=f"{run_id}-l25",
        r12_customer_field_outcome_feedback_update=feedback,
        replay_requested_at=rehearsal_started_at,
    )
    shadow_replay = load_json_artifact(shadow_replay_path)
    write_r12_customer_feedback_shadow_replay_holdout_review(
        output=holdout_review_path,
        artifact_id=(
            "r12-customer-feedback-shadow-replay-holdout-review-feedback-loop-rehearsal"
        ),
        run_id=f"{run_id}-l26",
        r12_customer_feedback_update_shadow_replay=shadow_replay,
        holdout_review_requested_at=rehearsal_started_at,
        independent_holdout_source_id="synthetic-feedback-loop-rehearsal-holdout",
        independent_holdout_case_count=contract["minimum_case_count"],
    )
    holdout_review = load_json_artifact(holdout_review_path)

    feedback_candidate_count = feedback["feedback_summary"]["candidate_count"]
    accepted_shadow_count = shadow_replay["shadow_replay_summary"][
        "accepted_candidate_count"
    ]
    synthetic_holdout_executed = holdout_review["holdout_review_summary"][
        "holdout_review_executed"
    ]
    synthetic_holdout_passed = holdout_review["holdout_review_summary"][
        "holdout_review_passed"
    ]

    report = {
        "schema_version": (
            R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_customer_feedback_loop_operator_rehearsal_ready_no_field_claim",
        "claim_level": (
            "synthetic_feedback_loop_rehearsal_only_no_customer_validation_claim"
        ),
        "rehearsal_summary": {
            "handoff_artifact_id": handoff["artifact_id"],
            "rehearsal_started_at": rehearsal_started_at,
            "sample_slice_kind": "synthetic_feedback_loop_rehearsal_fixture",
            "sample_slice_path": str(sample_slice_path),
            "case_count": contract["minimum_case_count"],
            "required_field_count": len(contract["required_fields"]),
            "intake_ready_for_revalidation": intake["acceptance_gates"][
                "ready_for_revalidation"
            ],
            "synthetic_metrics_computed": revalidation["acceptance_gates"][
                "metrics_computed"
            ],
            "synthetic_field_metrics_passed": revalidation["acceptance_gates"][
                "field_outcome_validated"
            ],
            "feedback_candidate_count": feedback_candidate_count,
            "shadow_replay_executed": shadow_replay["acceptance_gates"][
                "shadow_replay_executed"
            ],
            "accepted_shadow_candidate_count": accepted_shadow_count,
            "synthetic_holdout_review_executed": synthetic_holdout_executed,
            "synthetic_holdout_review_passed": synthetic_holdout_passed,
        },
        "pipeline_artifacts": {
            "intake_validation": _artifact_summary(intake, intake_path),
            "field_revalidation": _artifact_summary(revalidation, revalidation_path),
            "feedback_update": _artifact_summary(feedback, feedback_path),
            "shadow_replay": _artifact_summary(shadow_replay, shadow_replay_path),
            "holdout_review": _artifact_summary(holdout_review, holdout_review_path),
        },
        "acceptance_gates": {
            "synthetic_rehearsal_fixture_generated": sample_slice_path.exists(),
            "l22_intake_validator_executed": intake_path.exists(),
            "l23_field_revalidation_executed": revalidation_path.exists(),
            "l24_feedback_candidates_generated": feedback_candidate_count > 0,
            "l25_shadow_replay_executed": shadow_replay["acceptance_gates"][
                "shadow_replay_executed"
            ],
            "l26_synthetic_holdout_review_executed": synthetic_holdout_executed,
            "real_customer_field_slice_submitted": False,
            "real_independent_holdout_present": False,
            "field_outcome_validated": False,
            "metrics_computed_on_real_customer_slice": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": (
            "accept_feedback_loop_rehearsal_keep_customer_validation_blocked"
        ),
        "next_required_artifact": "real_customer_field_slice_or_public_target_outcome",
        "source_refs": [
            handoff["artifact_id"],
            intake["artifact_id"],
            revalidation["artifact_id"],
            feedback["artifact_id"],
            shadow_replay["artifact_id"],
            holdout_review["artifact_id"],
            f"synthetic_feedback_loop_rehearsal_slice:{sample_slice_path}",
        ],
        "source_registry": [
            {"artifact_id": handoff["artifact_id"], "path": handoff_path},
            *[
                {
                    "artifact_id": artifact["artifact_id"],
                    "path": str(path),
                }
                for artifact, path in [
                    (intake, intake_path),
                    (revalidation, revalidation_path),
                    (feedback, feedback_path),
                    (shadow_replay, shadow_replay_path),
                    (holdout_review, holdout_review_path),
                ]
            ],
            {
                "artifact_id": (
                    f"synthetic_feedback_loop_rehearsal_slice:{sample_slice_path}"
                ),
                "path": str(sample_slice_path),
            },
        ],
        "allowed_claims": [
            (
                "The L22-L26 customer feedback loop can be rehearsed locally "
                "on a synthetic field-slice fixture."
            ),
            (
                "The rehearsal exercises intake, field metrics, feedback "
                "candidate generation, shadow replay, and synthetic holdout "
                "review without changing Product defaults."
            ),
        ],
        "blocked_claims": [
            "real_customer_field_slice_validated=true",
            "real_independent_holdout_present=true",
            "metrics_computed_on_real_customer_slice=true",
            "field_outcome_validated=true",
            "Product default can use customer feedback loop by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_feedback_loop_operator_rehearsal(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_feedback_loop_operator_rehearsal(**kwargs),
    )


def _validate_l21_handoff(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION
    ):
        raise ValueError("r12 L21 handoff package schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L21 handoff package acceptance_gates required")
    if gates.get("customer_field_slice_contract_machine_checkable") is not True:
        raise ValueError("r12 L21 handoff must expose a machine-checkable contract")
    if gates.get("customer_data_request_ready") is not True:
        raise ValueError("r12 L21 handoff must be customer-data-request ready")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 L21 handoff must not compute metrics")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L21 handoff must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L21 handoff must block runtime default")


def _write_synthetic_feedback_loop_slice(
    *,
    path: Path,
    required_fields: list[str],
    case_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=required_fields)
        writer.writeheader()
        for idx in range(case_count):
            writer.writerow(
                {
                    field: _synthetic_field_value(field=field, idx=idx)
                    for field in required_fields
                }
            )


def _synthetic_field_value(*, field: str, idx: int) -> str:
    prediction = 0.10 + idx * 0.03
    values = {
        "case_id": f"feedback-rehearsal-case-{idx:03d}",
        "segment_id": f"segment-{idx % 3}",
        "scenario_id": "scenario-feedback-rehearsal-001",
        "prediction_share_or_score": f"{prediction:.3f}",
        "observed_outcome": f"{prediction + 0.02:.3f}",
        "outcome_timestamp": "2026-07-15T00:00:00Z",
        "customer_approval_reference": "synthetic-feedback-loop-rehearsal-approval",
    }
    return values.get(field, f"synthetic-{field}-{idx}")


def _artifact_summary(artifact: dict[str, Any], path: Path) -> dict[str, str]:
    return {
        "artifact_id": artifact["artifact_id"],
        "status": artifact["status"],
        "output_path": str(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-customer-field-slice-handoff-package-path",
        required=True,
    )
    parser.add_argument("--rehearsal-started-at", required=True)
    parser.add_argument("--rehearsal-work-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_feedback_loop_operator_rehearsal(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_customer_field_slice_handoff_package=load_json_artifact(
            args.r12_customer_field_slice_handoff_package_path
        ),
        r12_customer_field_slice_handoff_package_path=(
            args.r12_customer_field_slice_handoff_package_path
        ),
        rehearsal_started_at=args.rehearsal_started_at,
        rehearsal_work_dir=args.rehearsal_work_dir,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "accepted_shadow_candidate_count": artifact[
                    "rehearsal_summary"
                ]["accepted_shadow_candidate_count"],
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
                "synthetic_holdout_review_executed": artifact[
                    "rehearsal_summary"
                ]["synthetic_holdout_review_executed"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
