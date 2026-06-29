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
from experiments.r12_customer_feedback_shadow_replay_holdout_review import (
    R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION,
)
from experiments.r12_customer_feedback_update_shadow_replay import (
    R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION,
)
from experiments.r12_customer_field_outcome_feedback_update import (
    R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_handoff_package import (
    R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_intake_validation import (
    R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_revalidation import (
    R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION,
)
from experiments.r12_target_outcome_or_customer_field_slice_arrival import (
    R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION,
)


R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION = (
    "r12-customer-validation-workflow-status-v1"
)


def build_r12_customer_validation_workflow_status(
    *,
    artifact_id: str,
    run_id: str,
    workflow_generated_at: str,
    r12_target_outcome_or_customer_field_slice_arrival: dict[str, Any],
    r12_customer_field_slice_handoff_package: dict[str, Any],
    r12_customer_field_slice_intake_validation: dict[str, Any],
    r12_customer_field_slice_revalidation: dict[str, Any],
    r12_customer_field_outcome_feedback_update: dict[str, Any],
    r12_customer_feedback_update_shadow_replay: dict[str, Any],
    r12_customer_feedback_shadow_replay_holdout_review: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    workflow_generated_at = non_empty_string(
        workflow_generated_at,
        field="workflow_generated_at",
    )
    artifacts = {
        "l20": r12_target_outcome_or_customer_field_slice_arrival,
        "l21": r12_customer_field_slice_handoff_package,
        "l22": r12_customer_field_slice_intake_validation,
        "l23": r12_customer_field_slice_revalidation,
        "l24": r12_customer_field_outcome_feedback_update,
        "l25": r12_customer_feedback_update_shadow_replay,
        "l26": r12_customer_feedback_shadow_replay_holdout_review,
    }
    _validate_inputs(artifacts)

    l20_gates = artifacts["l20"]["acceptance_gates"]
    l21_gates = artifacts["l21"]["acceptance_gates"]
    l22_gates = artifacts["l22"]["acceptance_gates"]
    l23_gates = artifacts["l23"]["acceptance_gates"]
    l24_gates = artifacts["l24"]["acceptance_gates"]
    l25_gates = artifacts["l25"]["acceptance_gates"]
    l26_gates = artifacts["l26"]["acceptance_gates"]

    source_ready = bool(l20_gates["field_or_pre_outcome_revalidation_ready"])
    intake_ready = bool(l22_gates["ready_for_revalidation"])
    metrics_computed = bool(l23_gates["metrics_computed"])
    field_validated = bool(l23_gates["field_outcome_validated"])
    feedback_candidates_present = bool(l24_gates["candidate_updates_generated"])
    shadow_replay_executed = bool(l25_gates["shadow_replay_executed"])
    holdout_review_executed = bool(l26_gates["holdout_review_executed"])

    stage = _current_stage(
        source_ready=source_ready,
        intake_ready=intake_ready,
        metrics_computed=metrics_computed,
        feedback_candidates_present=feedback_candidates_present,
        shadow_replay_executed=shadow_replay_executed,
        holdout_review_executed=holdout_review_executed,
    )
    status, claim_level, next_artifact = _status_tuple(stage)
    workflow_steps = _workflow_steps(
        artifacts=artifacts,
        source_ready=source_ready,
        intake_ready=intake_ready,
        metrics_computed=metrics_computed,
        feedback_candidates_present=feedback_candidates_present,
        shadow_replay_executed=shadow_replay_executed,
        holdout_review_executed=holdout_review_executed,
    )
    report = {
        "schema_version": R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "workflow_summary": {
            "workflow_generated_at": workflow_generated_at,
            "current_stage": stage["current_stage"],
            "next_action": stage["next_action"],
            "blocking_artifact_id": stage["blocking_artifact_id"],
            "source_arrived": source_ready,
            "customer_slice_ready_for_revalidation": intake_ready,
            "metrics_computed": metrics_computed,
            "field_outcome_validated": field_validated,
            "feedback_candidate_count": artifacts["l24"]["feedback_summary"][
                "candidate_count"
            ],
            "shadow_replay_executed": shadow_replay_executed,
            "holdout_review_executed": holdout_review_executed,
        },
        "workflow_steps": workflow_steps,
        "operator_runbook": _operator_runbook(),
        "acceptance_gates": {
            "workflow_status_package_ready": True,
            "source_arrival_gate_ready": bool(
                l21_gates["source_arrival_gate_ready"]
            ),
            "customer_data_request_ready": bool(
                l21_gates["customer_data_request_ready"]
            ),
            "customer_slice_ready_for_revalidation": intake_ready,
            "field_outcome_validated": field_validated,
            "feedback_candidates_present": feedback_candidates_present,
            "shadow_replay_executed": shadow_replay_executed,
            "holdout_review_executed": holdout_review_executed,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": next_artifact,
        "source_refs": [artifact["artifact_id"] for artifact in artifacts.values()],
        "source_registry": _source_registry(artifacts),
        "allowed_claims": [
            (
                "Customer validation workflow status is source-backed and "
                "machine-checkable."
            ),
            (
                "Product can show the current customer validation stage and "
                "operator runbook without claiming field validation."
            ),
        ],
        "blocked_claims": [
            "field validation 已完成",
            "customer field validation passed",
            "feedback update is accepted for Product default",
            "Product default can use customer feedback updates",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_validation_workflow_status(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_validation_workflow_status(**kwargs),
    )


def _validate_inputs(artifacts: dict[str, dict[str, Any]]) -> None:
    expected_versions = {
        "l20": R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION,
        "l21": R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
        "l22": R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION,
        "l23": R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION,
        "l24": R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
        "l25": R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION,
        "l26": R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION,
    }
    for key, artifact in artifacts.items():
        if artifact.get("schema_version") != expected_versions[key]:
            raise ValueError(f"r12 {key} schema_version is invalid")
        gates = artifact.get("acceptance_gates")
        if not isinstance(gates, dict):
            raise ValueError(f"r12 {key} acceptance_gates required")
        if gates.get("product_default_allowed") is not False:
            raise ValueError(f"r12 {key} must block Product default")
        if gates.get("runtime_default_allowed") is not False:
            raise ValueError(f"r12 {key} must block runtime default")


def _current_stage(
    *,
    source_ready: bool,
    intake_ready: bool,
    metrics_computed: bool,
    feedback_candidates_present: bool,
    shadow_replay_executed: bool,
    holdout_review_executed: bool,
) -> dict[str, str]:
    if not source_ready:
        return {
            "current_stage": "source_arrival_pending",
            "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
            "blocking_artifact_id": (
                "r12-target-outcome-or-customer-field-slice-arrival-current-001"
            ),
        }
    if not intake_ready:
        return {
            "current_stage": "intake_pending",
            "next_action": "run_customer_field_slice_intake_validation",
            "blocking_artifact_id": (
                "r12-customer-field-slice-intake-validation-current-001"
            ),
        }
    if not metrics_computed:
        return {
            "current_stage": "field_revalidation_pending",
            "next_action": "run_customer_field_slice_revalidation",
            "blocking_artifact_id": (
                "r12-customer-field-slice-revalidation-current-001"
            ),
        }
    if not feedback_candidates_present:
        return {
            "current_stage": "feedback_update_pending",
            "next_action": "run_customer_field_outcome_feedback_update",
            "blocking_artifact_id": (
                "r12-customer-field-outcome-feedback-update-current-001"
            ),
        }
    if not shadow_replay_executed:
        return {
            "current_stage": "shadow_replay_pending",
            "next_action": "run_customer_feedback_update_shadow_replay",
            "blocking_artifact_id": (
                "r12-customer-feedback-update-shadow-replay-current-001"
            ),
        }
    if not holdout_review_executed:
        return {
            "current_stage": "holdout_review_pending",
            "next_action": "run_customer_feedback_shadow_replay_holdout_review",
            "blocking_artifact_id": (
                "r12-customer-feedback-shadow-replay-holdout-review-current-001"
            ),
        }
    return {
        "current_stage": "governed_review_ready",
        "next_action": "run_human_governed_product_default_review",
        "blocking_artifact_id": (
            "customer-feedback-holdout-review-governance-decision"
        ),
    }


def _status_tuple(stage: dict[str, str]) -> tuple[str, str, str]:
    stage_id = stage["current_stage"]
    if stage_id == "source_arrival_pending":
        return (
            "r12_customer_validation_workflow_waiting_for_source",
            "customer_validation_workflow_ready_source_pending",
            "customer_field_slice_submission_or_target_outcome_artifact",
        )
    if stage_id == "intake_pending":
        return (
            "r12_customer_validation_workflow_waiting_for_intake",
            "customer_validation_workflow_ready_intake_pending",
            "r12_customer_field_slice_intake_validation",
        )
    if stage_id == "field_revalidation_pending":
        return (
            "r12_customer_validation_workflow_waiting_for_field_revalidation",
            "customer_validation_workflow_ready_field_revalidation_pending",
            "r12_customer_field_slice_revalidation",
        )
    if stage_id == "feedback_update_pending":
        return (
            "r12_customer_validation_workflow_waiting_for_feedback_update",
            "customer_validation_workflow_ready_feedback_update_pending",
            "r12_customer_field_outcome_feedback_update",
        )
    if stage_id == "shadow_replay_pending":
        return (
            "r12_customer_validation_workflow_waiting_for_shadow_replay",
            "customer_validation_workflow_ready_shadow_replay_pending",
            "r12_customer_feedback_update_shadow_replay",
        )
    if stage_id == "holdout_review_pending":
        return (
            "r12_customer_validation_workflow_waiting_for_holdout_review",
            "customer_validation_workflow_ready_holdout_review_pending",
            "r12_customer_feedback_shadow_replay_holdout_review",
        )
    return (
        "r12_customer_validation_workflow_governed_review_ready",
        "customer_validation_workflow_ready_governed_review_required",
        "customer_feedback_holdout_review_governance_decision",
    )


def _workflow_steps(
    *,
    artifacts: dict[str, dict[str, Any]],
    source_ready: bool,
    intake_ready: bool,
    metrics_computed: bool,
    feedback_candidates_present: bool,
    shadow_replay_executed: bool,
    holdout_review_executed: bool,
) -> list[dict[str, Any]]:
    return [
        _step(
            "source_arrival",
            artifacts["l20"],
            "ready" if source_ready else "pending",
            artifacts["l20"]["next_required_artifact"],
        ),
        _step(
            "handoff_package",
            artifacts["l21"],
            "ready",
            artifacts["l21"]["next_required_artifact"],
        ),
        _step(
            "intake_validation",
            artifacts["l22"],
            _dependent_status(
                prerequisite_ready=source_ready,
                current_ready=intake_ready,
            ),
            artifacts["l22"]["next_required_artifact"],
        ),
        _step(
            "field_revalidation",
            artifacts["l23"],
            _dependent_status(
                prerequisite_ready=intake_ready,
                current_ready=metrics_computed,
            ),
            artifacts["l23"]["next_required_artifact"],
        ),
        _step(
            "feedback_update_candidate",
            artifacts["l24"],
            _dependent_status(
                prerequisite_ready=metrics_computed,
                current_ready=feedback_candidates_present,
            ),
            artifacts["l24"]["next_required_artifact"],
        ),
        _step(
            "shadow_replay",
            artifacts["l25"],
            _dependent_status(
                prerequisite_ready=feedback_candidates_present,
                current_ready=shadow_replay_executed,
            ),
            artifacts["l25"]["next_required_artifact"],
        ),
        _step(
            "holdout_review",
            artifacts["l26"],
            _dependent_status(
                prerequisite_ready=shadow_replay_executed,
                current_ready=holdout_review_executed,
            ),
            artifacts["l26"]["next_required_artifact"],
        ),
    ]


def _step(
    step_id: str,
    artifact: dict[str, Any],
    step_status: str,
    next_required_artifact: str,
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "step_status": step_status,
        "artifact_id": artifact["artifact_id"],
        "artifact_status": artifact["status"],
        "next_required_artifact": next_required_artifact,
    }


def _dependent_status(*, prerequisite_ready: bool, current_ready: bool) -> str:
    if current_ready:
        return "ready"
    if prerequisite_ready:
        return "pending"
    return "blocked"


def _operator_runbook() -> dict[str, Any]:
    return {
        "runbook_id": "r12_customer_validation_workflow_operator_runbook",
        "commands_after_source_arrival": [
            {
                "step_id": "intake_validation",
                "command": (
                    ".venv/bin/python "
                    "experiments/r12_customer_field_slice_intake_validation.py "
                    "--customer-field-slice-path <customer-slice.csv>"
                ),
            },
            {
                "step_id": "field_revalidation",
                "command": (
                    ".venv/bin/python "
                    "experiments/r12_customer_field_slice_revalidation.py "
                    "--r12-customer-field-slice-intake-validation-path "
                    "<intake-artifact.json>"
                ),
            },
            {
                "step_id": "feedback_update_candidate",
                "command": (
                    ".venv/bin/python "
                    "experiments/r12_customer_field_outcome_feedback_update.py "
                    "--r12-customer-field-slice-revalidation-path "
                    "<revalidation-artifact.json>"
                ),
            },
            {
                "step_id": "shadow_replay",
                "command": (
                    ".venv/bin/python "
                    "experiments/r12_customer_feedback_update_shadow_replay.py "
                    "--r12-customer-field-outcome-feedback-update-path "
                    "<feedback-update-artifact.json>"
                ),
            },
            {
                "step_id": "holdout_review",
                "command": (
                    ".venv/bin/python "
                    "experiments/r12_customer_feedback_shadow_replay_holdout_review.py "
                    "--r12-customer-feedback-update-shadow-replay-path "
                    "<shadow-replay-artifact.json>"
                ),
            },
        ],
        "manual_approval_points": [
            "customer_approval_reference_required_before_intake",
            "governed_review_required_after_holdout_review",
        ],
    }


def _source_registry(artifacts: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    paths = {
        "l20": (
            "experiments/results/"
            "r12_target_outcome_or_customer_field_slice_arrival/"
            "r12-target-outcome-or-customer-field-slice-arrival-current-001.json"
        ),
        "l21": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-handoff-package-current-001.json"
        ),
        "l22": (
            "experiments/results/r12_customer_field_slice_intake_validation/"
            "r12-customer-field-slice-intake-validation-current-001.json"
        ),
        "l23": (
            "experiments/results/r12_customer_field_slice_revalidation/"
            "r12-customer-field-slice-revalidation-current-001.json"
        ),
        "l24": (
            "experiments/results/r12_customer_field_outcome_feedback_update/"
            "r12-customer-field-outcome-feedback-update-current-001.json"
        ),
        "l25": (
            "experiments/results/r12_customer_feedback_update_shadow_replay/"
            "r12-customer-feedback-update-shadow-replay-current-001.json"
        ),
        "l26": (
            "experiments/results/"
            "r12_customer_feedback_shadow_replay_holdout_review/"
            "r12-customer-feedback-shadow-replay-holdout-review-current-001.json"
        ),
    }
    return [
        {
            "artifact_id": artifacts[key]["artifact_id"],
            "path": path,
        }
        for key, path in paths.items()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--workflow-generated-at", required=True)
    parser.add_argument(
        "--r12-target-outcome-or-customer-field-slice-arrival-path",
        required=True,
    )
    parser.add_argument("--r12-customer-field-slice-handoff-package-path", required=True)
    parser.add_argument("--r12-customer-field-slice-intake-validation-path", required=True)
    parser.add_argument("--r12-customer-field-slice-revalidation-path", required=True)
    parser.add_argument("--r12-customer-field-outcome-feedback-update-path", required=True)
    parser.add_argument("--r12-customer-feedback-update-shadow-replay-path", required=True)
    parser.add_argument(
        "--r12-customer-feedback-shadow-replay-holdout-review-path",
        required=True,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_validation_workflow_status(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        workflow_generated_at=args.workflow_generated_at,
        r12_target_outcome_or_customer_field_slice_arrival=load_json_artifact(
            args.r12_target_outcome_or_customer_field_slice_arrival_path
        ),
        r12_customer_field_slice_handoff_package=load_json_artifact(
            args.r12_customer_field_slice_handoff_package_path
        ),
        r12_customer_field_slice_intake_validation=load_json_artifact(
            args.r12_customer_field_slice_intake_validation_path
        ),
        r12_customer_field_slice_revalidation=load_json_artifact(
            args.r12_customer_field_slice_revalidation_path
        ),
        r12_customer_field_outcome_feedback_update=load_json_artifact(
            args.r12_customer_field_outcome_feedback_update_path
        ),
        r12_customer_feedback_update_shadow_replay=load_json_artifact(
            args.r12_customer_feedback_update_shadow_replay_path
        ),
        r12_customer_feedback_shadow_replay_holdout_review=load_json_artifact(
            args.r12_customer_feedback_shadow_replay_holdout_review_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "current_stage": artifact["workflow_summary"]["current_stage"],
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
