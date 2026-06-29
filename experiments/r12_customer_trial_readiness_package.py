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
from experiments.r12_customer_field_slice_handoff_package import (
    R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
)
from experiments.r12_customer_validation_workflow_status import (
    R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION,
)


R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION = (
    "r12-customer-trial-readiness-package-v1"
)


def build_r12_customer_trial_readiness_package(
    *,
    artifact_id: str,
    run_id: str,
    package_generated_at: str,
    r12_customer_field_slice_handoff_package: dict[str, Any],
    r12_customer_validation_workflow_status: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    package_generated_at = non_empty_string(
        package_generated_at,
        field="package_generated_at",
    )
    _validate_handoff(r12_customer_field_slice_handoff_package)
    _validate_workflow(r12_customer_validation_workflow_status)

    handoff = r12_customer_field_slice_handoff_package
    workflow = r12_customer_validation_workflow_status
    handoff_summary = handoff["handoff_summary"]
    workflow_summary = workflow["workflow_summary"]
    field_contract = handoff["field_slice_contract"]
    workflow_gates = workflow["acceptance_gates"]

    report = {
        "schema_version": R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_customer_trial_readiness_package_ready_guarded_source_pending",
        "claim_level": "customer_trial_readiness_package_ready_no_validation_claim",
        "trial_readiness_summary": {
            "package_generated_at": package_generated_at,
            "current_stage": workflow_summary["current_stage"],
            "next_action": workflow_summary["next_action"],
            "customer_data_request_ready": handoff["acceptance_gates"][
                "customer_data_request_ready"
            ],
            "template_output_path": handoff_summary["template_output_path"],
            "minimum_case_count": field_contract["minimum_case_count"],
            "required_field_count": len(field_contract["required_fields"]),
            "manual_approval_point_count": len(
                workflow["operator_runbook"]["manual_approval_points"]
            ),
            "field_outcome_validated": workflow_gates["field_outcome_validated"],
        },
        "customer_trial_checklist": _customer_trial_checklist(handoff),
        "operator_runbook": workflow["operator_runbook"],
        "privacy_and_approval_contract": handoff[
            "privacy_and_approval_contract"
        ],
        "acceptance_gates": {
            "trial_readiness_package_ready": True,
            "customer_data_request_ready": handoff["acceptance_gates"][
                "customer_data_request_ready"
            ],
            "workflow_status_package_ready": workflow_gates[
                "workflow_status_package_ready"
            ],
            "customer_slice_ready_for_revalidation": workflow_gates[
                "customer_slice_ready_for_revalidation"
            ],
            "field_outcome_validated": workflow_gates["field_outcome_validated"],
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": workflow["next_required_artifact"],
        "source_refs": [
            handoff["artifact_id"],
            workflow["artifact_id"],
            *handoff.get("source_refs", []),
        ],
        "source_registry": _source_registry(handoff, workflow),
        "allowed_claims": [
            (
                "Product can provide a customer trial readiness package with "
                "source-backed data requirements and operator runbook."
            ),
            (
                "The package is ready for customer field-slice collection, but "
                "does not claim field validation."
            ),
        ],
        "blocked_claims": [
            "field validation 已完成",
            "customer field validation passed",
            "customer trial has produced accepted feedback update",
            "Product default can use customer trial output",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_trial_readiness_package(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_trial_readiness_package(**kwargs),
    )


def _validate_handoff(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION
    ):
        raise ValueError("r12 L21 handoff package schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L21 handoff package acceptance_gates required")
    if gates.get("customer_data_request_ready") is not True:
        raise ValueError("r12 L21 customer data request must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L21 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L21 must block runtime default")


def _validate_workflow(artifact: dict[str, Any]) -> None:
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


def _customer_trial_checklist(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    fields = handoff["field_slice_contract"]["required_fields"]
    return [
        {
            "check_id": "customer_approval_reference",
            "required": True,
            "description": "Every row must include customer_approval_reference.",
            "source_field": "customer_approval_reference",
        },
        {
            "check_id": "pseudonymous_case_ids",
            "required": True,
            "description": "case_id must be stable and pseudonymous; direct PII is blocked.",
            "source_field": "case_id",
        },
        {
            "check_id": "minimum_case_count",
            "required": True,
            "description": (
                f"At least {handoff['field_slice_contract']['minimum_case_count']} "
                "cases are required before revalidation."
            ),
            "source_field": "case_count",
        },
        {
            "check_id": "required_fields",
            "required": True,
            "description": "Customer slice must include all required schema fields.",
            "source_field": ",".join(fields),
        },
        {
            "check_id": "run_intake_validation",
            "required": True,
            "description": "Run intake validation before any field metrics or update candidate.",
            "source_field": "r12_customer_field_slice_intake_validation",
        },
    ]


def _source_registry(
    handoff: dict[str, Any],
    workflow: dict[str, Any],
) -> list[dict[str, str]]:
    registry = [
        {
            "artifact_id": handoff["artifact_id"],
            "path": (
                "experiments/results/r12_customer_field_slice_handoff_package/"
                "r12-customer-field-slice-handoff-package-current-001.json"
            ),
        },
        {
            "artifact_id": workflow["artifact_id"],
            "path": (
                "experiments/results/r12_customer_validation_workflow_status/"
                "r12-customer-validation-workflow-status-current-001.json"
            ),
        },
    ]
    for entry in handoff.get("source_registry", []):
        if entry not in registry:
            registry.append(entry)
    return registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--package-generated-at", required=True)
    parser.add_argument(
        "--r12-customer-field-slice-handoff-package-path",
        required=True,
    )
    parser.add_argument(
        "--r12-customer-validation-workflow-status-path",
        required=True,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_trial_readiness_package(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        package_generated_at=args.package_generated_at,
        r12_customer_field_slice_handoff_package=load_json_artifact(
            args.r12_customer_field_slice_handoff_package_path
        ),
        r12_customer_validation_workflow_status=load_json_artifact(
            args.r12_customer_validation_workflow_status_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "current_stage": artifact["trial_readiness_summary"][
                    "current_stage"
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
