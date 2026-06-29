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
from experiments.r12_customer_trial_evidence_ledger import (
    R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION,
)
from experiments.r12_customer_validation_workflow_status import (
    R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION,
)


R12_REAL_SOURCE_VALIDATION_EXECUTION_PACKET_SCHEMA_VERSION = (
    "r12-real-source-validation-execution-packet-v1"
)


def build_r12_real_source_validation_execution_packet(
    *,
    artifact_id: str,
    run_id: str,
    packet_created_at: str,
    r12_customer_validation_workflow_status: dict[str, Any],
    r12_customer_validation_workflow_status_path: str | Path,
    r12_customer_trial_evidence_ledger: dict[str, Any],
    r12_customer_trial_evidence_ledger_path: str | Path,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    packet_created_at = non_empty_string(
        packet_created_at,
        field="packet_created_at",
    )
    workflow_path = non_empty_string(
        str(r12_customer_validation_workflow_status_path),
        field="r12_customer_validation_workflow_status_path",
    )
    ledger_path = non_empty_string(
        str(r12_customer_trial_evidence_ledger_path),
        field="r12_customer_trial_evidence_ledger_path",
    )
    _validate_workflow_status(r12_customer_validation_workflow_status)
    _validate_evidence_ledger(r12_customer_trial_evidence_ledger)

    workflow = r12_customer_validation_workflow_status
    ledger = r12_customer_trial_evidence_ledger
    workflow_summary = workflow["workflow_summary"]
    ledger_summary = ledger["ledger_summary"]
    blocking_gap_count = int(ledger_summary["blocking_gap_count"])
    execution_steps = _execution_steps()

    report = {
        "schema_version": R12_REAL_SOURCE_VALIDATION_EXECUTION_PACKET_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_real_source_validation_execution_packet_ready_source_pending"
        ),
        "claim_level": "real_source_execution_packet_ready_no_validation_claim",
        "execution_summary": {
            "packet_created_at": packet_created_at,
            "workflow_artifact_id": workflow["artifact_id"],
            "evidence_ledger_artifact_id": ledger["artifact_id"],
            "current_stage": workflow_summary["current_stage"],
            "next_action": workflow_summary["next_action"],
            "source_arrived": False,
            "execution_chain_declared": True,
            "executable_step_count": len(execution_steps),
            "manual_approval_point_count": sum(
                1 for step in execution_steps if step["requires_manual_approval"]
            ),
            "blocking_gap_count": blocking_gap_count,
            "next_required_artifact": ledger["next_required_artifact"],
        },
        "source_modes": [
            {
                "source_mode": "customer_field_slice",
                "required_placeholder": "CUSTOMER_FIELD_SLICE_PATH",
                "accepted_formats": ["csv", "jsonl"],
                "minimum_case_count": 10,
                "approval_reference_required": True,
            },
            {
                "source_mode": "public_target_outcome",
                "required_placeholder": "PUBLIC_TARGET_OUTCOME_ARTIFACT_PATH",
                "accepted_formats": ["json"],
                "minimum_case_count": 10,
                "approval_reference_required": False,
            },
        ],
        "execution_steps": execution_steps,
        "acceptance_gates": {
            "real_source_validation_execution_packet_ready": True,
            "workflow_status_package_ready": workflow["acceptance_gates"][
                "workflow_status_package_ready"
            ],
            "customer_trial_evidence_ledger_ready": ledger["acceptance_gates"][
                "customer_trial_evidence_ledger_ready"
            ],
            "execution_chain_declared": True,
            "source_arrived": False,
            "metrics_computed_on_real_customer_slice": False,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": ledger["next_required_artifact"],
        "source_refs": [workflow["artifact_id"], ledger["artifact_id"]],
        "source_registry": [
            {
                "artifact_id": workflow["artifact_id"],
                "path": workflow_path,
            },
            {
                "artifact_id": ledger["artifact_id"],
                "path": ledger_path,
            },
        ],
        "allowed_claims": [
            (
                "Operators have a complete source-arrival execution packet for "
                "L22-L26 validation."
            ),
            (
                "The packet is a runbook and does not claim field validation or "
                "runtime default readiness."
            ),
        ],
        "blocked_claims": [
            "source_arrived=true",
            "metrics_computed_on_real_customer_slice=true",
            "field_outcome_validated=true",
            "customer field validation passed",
            "Product default can use customer feedback updates",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_real_source_validation_execution_packet(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_real_source_validation_execution_packet(**kwargs),
    )


def _validate_workflow_status(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION
    ):
        raise ValueError("r12 L27 workflow status schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L27 workflow status acceptance_gates required")
    if gates.get("workflow_status_package_ready") is not True:
        raise ValueError("r12 L27 workflow status package must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L27 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L27 must block runtime default")


def _validate_evidence_ledger(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION
    ):
        raise ValueError("r12 L36 evidence ledger schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L36 evidence ledger acceptance_gates required")
    if gates.get("customer_trial_evidence_ledger_ready") is not True:
        raise ValueError("r12 L36 evidence ledger must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L36 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L36 must block runtime default")


def _execution_steps() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "l22_intake_validation",
            "requires_source_arrival": True,
            "requires_manual_approval": True,
            "input_artifact_placeholder": "CUSTOMER_FIELD_SLICE_PATH",
            "output_artifact_path": (
                "experiments/results/r12_customer_field_slice_intake_validation/"
                "r12-customer-field-slice-intake-validation-customer-001.json"
            ),
            "command_template": (
                ".venv/bin/python experiments/r12_customer_field_slice_intake_validation.py "
                "--artifact-id r12-customer-field-slice-intake-validation-customer-001 "
                "--run-id r12-customer-field-slice-intake-customer-001 "
                "--r12-customer-field-slice-handoff-package-path "
                "experiments/results/r12_customer_field_slice_handoff_package/"
                "r12-customer-field-slice-handoff-package-current-001.json "
                "--intake-checked-at CUSTOMER_FIELD_SLICE_INTAKE_TIMESTAMP "
                "--customer-field-slice-path CUSTOMER_FIELD_SLICE_PATH "
                "--output experiments/results/r12_customer_field_slice_intake_validation/"
                "r12-customer-field-slice-intake-validation-customer-001.json"
            ),
        },
        {
            "step_id": "l23_field_revalidation",
            "requires_source_arrival": True,
            "requires_manual_approval": False,
            "input_artifact_placeholder": (
                "r12-customer-field-slice-intake-validation-customer-001.json"
            ),
            "output_artifact_path": (
                "experiments/results/r12_customer_field_slice_revalidation/"
                "r12-customer-field-slice-revalidation-customer-001.json"
            ),
            "command_template": (
                ".venv/bin/python experiments/r12_customer_field_slice_revalidation.py "
                "--artifact-id r12-customer-field-slice-revalidation-customer-001 "
                "--run-id r12-customer-field-slice-revalidation-customer-001 "
                "--r12-customer-field-slice-intake-validation-path "
                "experiments/results/r12_customer_field_slice_intake_validation/"
                "r12-customer-field-slice-intake-validation-customer-001.json "
                "--revalidation-checked-at CUSTOMER_FIELD_REVALIDATION_TIMESTAMP "
                "--output experiments/results/r12_customer_field_slice_revalidation/"
                "r12-customer-field-slice-revalidation-customer-001.json"
            ),
        },
        {
            "step_id": "l24_feedback_update_candidate",
            "requires_source_arrival": True,
            "requires_manual_approval": False,
            "input_artifact_placeholder": (
                "r12-customer-field-slice-revalidation-customer-001.json"
            ),
            "output_artifact_path": (
                "experiments/results/r12_customer_field_outcome_feedback_update/"
                "r12-customer-field-outcome-feedback-update-customer-001.json"
            ),
            "command_template": (
                ".venv/bin/python experiments/r12_customer_field_outcome_feedback_update.py "
                "--artifact-id r12-customer-field-outcome-feedback-update-customer-001 "
                "--run-id r12-customer-field-outcome-feedback-update-customer-001 "
                "--r12-customer-field-slice-revalidation-path "
                "experiments/results/r12_customer_field_slice_revalidation/"
                "r12-customer-field-slice-revalidation-customer-001.json "
                "--feedback-generated-at CUSTOMER_FEEDBACK_UPDATE_TIMESTAMP "
                "--output experiments/results/r12_customer_field_outcome_feedback_update/"
                "r12-customer-field-outcome-feedback-update-customer-001.json"
            ),
        },
        {
            "step_id": "l25_shadow_replay",
            "requires_source_arrival": True,
            "requires_manual_approval": False,
            "input_artifact_placeholder": (
                "r12-customer-field-outcome-feedback-update-customer-001.json"
            ),
            "output_artifact_path": (
                "experiments/results/r12_customer_feedback_update_shadow_replay/"
                "r12-customer-feedback-update-shadow-replay-customer-001.json"
            ),
            "command_template": (
                ".venv/bin/python experiments/r12_customer_feedback_update_shadow_replay.py "
                "--artifact-id r12-customer-feedback-update-shadow-replay-customer-001 "
                "--run-id r12-customer-feedback-update-shadow-replay-customer-001 "
                "--r12-customer-field-outcome-feedback-update-path "
                "experiments/results/r12_customer_field_outcome_feedback_update/"
                "r12-customer-field-outcome-feedback-update-customer-001.json "
                "--replay-requested-at CUSTOMER_SHADOW_REPLAY_TIMESTAMP "
                "--output experiments/results/r12_customer_feedback_update_shadow_replay/"
                "r12-customer-feedback-update-shadow-replay-customer-001.json"
            ),
        },
        {
            "step_id": "l26_holdout_review",
            "requires_source_arrival": True,
            "requires_manual_approval": True,
            "input_artifact_placeholder": (
                "r12-customer-feedback-update-shadow-replay-customer-001.json"
            ),
            "output_artifact_path": (
                "experiments/results/r12_customer_feedback_shadow_replay_holdout_review/"
                "r12-customer-feedback-shadow-replay-holdout-review-customer-001.json"
            ),
            "command_template": (
                ".venv/bin/python experiments/r12_customer_feedback_shadow_replay_holdout_review.py "
                "--artifact-id r12-customer-feedback-shadow-replay-holdout-review-customer-001 "
                "--run-id r12-customer-feedback-shadow-replay-holdout-review-customer-001 "
                "--r12-customer-feedback-update-shadow-replay-path "
                "experiments/results/r12_customer_feedback_update_shadow_replay/"
                "r12-customer-feedback-update-shadow-replay-customer-001.json "
                "--holdout-review-requested-at CUSTOMER_HOLDOUT_REVIEW_TIMESTAMP "
                "--output experiments/results/r12_customer_feedback_shadow_replay_holdout_review/"
                "r12-customer-feedback-shadow-replay-holdout-review-customer-001.json"
            ),
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--packet-created-at", required=True)
    parser.add_argument("--r12-customer-validation-workflow-status-path", required=True)
    parser.add_argument("--r12-customer-trial-evidence-ledger-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    workflow = load_json_artifact(args.r12_customer_validation_workflow_status_path)
    ledger = load_json_artifact(args.r12_customer_trial_evidence_ledger_path)
    output_path = write_r12_real_source_validation_execution_packet(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        packet_created_at=args.packet_created_at,
        r12_customer_validation_workflow_status=workflow,
        r12_customer_validation_workflow_status_path=(
            args.r12_customer_validation_workflow_status_path
        ),
        r12_customer_trial_evidence_ledger=ledger,
        r12_customer_trial_evidence_ledger_path=(
            args.r12_customer_trial_evidence_ledger_path
        ),
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "execution_step_count": len(artifact["execution_steps"]),
                "output": str(output_path),
                "status": artifact["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
