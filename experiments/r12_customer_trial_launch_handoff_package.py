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
from experiments.r12_customer_trial_operational_check import (
    R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_readiness_package import (
    R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION,
)


R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION = (
    "r12-customer-trial-launch-handoff-package-v1"
)


def build_r12_customer_trial_launch_handoff_package(
    *,
    artifact_id: str,
    run_id: str,
    generated_at: str,
    r12_customer_trial_readiness_package: dict[str, Any],
    r12_customer_trial_operational_check: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    generated_at = non_empty_string(generated_at, field="generated_at")
    _validate_trial_readiness_package(r12_customer_trial_readiness_package)
    _validate_operational_check(r12_customer_trial_operational_check)

    readiness = r12_customer_trial_readiness_package
    operational = r12_customer_trial_operational_check
    readiness_summary = readiness["trial_readiness_summary"]
    operational_summary = operational["operational_summary"]
    operational_gates = operational["acceptance_gates"]
    required_fields = operational["template_check"]["required_fields"]
    operator_steps = [
        item["step_id"] for item in operational["operator_command_check"]
    ]
    first_command = operational["operator_command_check"][0]
    launch_ready = (
        readiness["acceptance_gates"]["trial_readiness_package_ready"]
        and operational_gates["customer_trial_request_operationally_ready"]
    )

    report = {
        "schema_version": R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_customer_trial_launch_handoff_package_ready_source_pending",
        "claim_level": "customer_trial_launch_ready_no_validation_claim",
        "launch_summary": {
            "generated_at": generated_at,
            "trial_readiness_artifact_id": readiness["artifact_id"],
            "operational_check_artifact_id": operational["artifact_id"],
            "current_stage": operational_summary["current_stage"],
            "next_action": operational_summary["next_action"],
            "launch_handoff_ready": launch_ready,
            "template_path": operational_summary["template_path"],
            "minimum_case_count": readiness_summary["minimum_case_count"],
            "required_field_count": len(required_fields),
            "operator_command_count": operational_summary[
                "operator_command_count"
            ],
            "manual_approval_point_count": operational_summary[
                "manual_approval_point_count"
            ],
            "field_outcome_validated": operational_gates[
                "field_outcome_validated"
            ],
        },
        "customer_launch_bundle": _customer_launch_bundle(),
        "customer_data_request": {
            "request_id": "r12_customer_field_slice_submission_request",
            "minimum_case_count": readiness_summary["minimum_case_count"],
            "required_fields": required_fields,
            "template_path": operational_summary["template_path"],
            "approval_reference_required": _approval_reference_required(
                readiness["customer_trial_checklist"]
            ),
            "direct_personal_identifiers_allowed": readiness[
                "privacy_and_approval_contract"
            ]["direct_personal_identifiers_allowed"],
        },
        "submission_instructions": {
            "next_required_artifact": operational["next_required_artifact"],
            "first_operator_step": first_command["step_id"],
            "first_operator_command": first_command["command"],
            "operator_step_ids": operator_steps,
        },
        "approval_and_governance": {
            "manual_approval_points": readiness["operator_runbook"][
                "manual_approval_points"
            ],
            "direct_personal_identifiers_allowed": readiness[
                "privacy_and_approval_contract"
            ]["direct_personal_identifiers_allowed"],
            "manual_prompt_or_persona_patch_allowed": readiness[
                "privacy_and_approval_contract"
            ]["manual_prompt_or_persona_patch_allowed"],
        },
        "acceptance_gates": {
            "launch_handoff_package_ready": launch_ready,
            "trial_readiness_package_ready": readiness["acceptance_gates"][
                "trial_readiness_package_ready"
            ],
            "operational_check_ready": operational_gates[
                "customer_trial_request_operationally_ready"
            ],
            "customer_trial_request_operationally_ready": operational_gates[
                "customer_trial_request_operationally_ready"
            ],
            "customer_field_slice_present": False,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": operational["next_required_artifact"],
        "source_refs": _source_refs(readiness, operational),
        "source_registry": _source_registry(readiness, operational),
        "allowed_claims": [
            (
                "Product can hand off a source-backed customer trial launch "
                "package with data request, template, approvals, and operator "
                "instructions."
            ),
            (
                "The launch package is ready to request customer field-slice "
                "submission, but does not claim field validation."
            ),
        ],
        "blocked_claims": [
            "field validation 已完成",
            "customer field validation passed",
            "customer trial produced accepted feedback update",
            "Product default can use customer trial output",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_trial_launch_handoff_package(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_trial_launch_handoff_package(**kwargs),
    )


def _validate_trial_readiness_package(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION
    ):
        raise ValueError("r12 L28 trial readiness package schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L28 trial readiness package acceptance_gates required")
    if gates.get("trial_readiness_package_ready") is not True:
        raise ValueError("r12 L28 trial readiness package must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L28 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L28 must block runtime default")


def _validate_operational_check(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION
    ):
        raise ValueError("r12 L29 operational check schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L29 operational check acceptance_gates required")
    if gates.get("customer_trial_request_operationally_ready") is not True:
        raise ValueError("r12 L29 operational check must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L29 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L29 must block runtime default")


def _customer_launch_bundle() -> list[dict[str, str]]:
    return [
        {
            "bundle_item_id": "data_request_brief",
            "description": "Customer-facing request for field-slice submission.",
        },
        {
            "bundle_item_id": "field_slice_template",
            "description": "Machine-checkable CSV template with required fields.",
        },
        {
            "bundle_item_id": "approval_checklist",
            "description": "Approval and privacy checks required before intake.",
        },
        {
            "bundle_item_id": "submission_and_runbook",
            "description": "Operator command sequence after source arrival.",
        },
        {
            "bundle_item_id": "claim_boundary",
            "description": "Blocked claims and runtime-default guardrails.",
        },
    ]


def _approval_reference_required(checklist: list[dict[str, Any]]) -> bool:
    return any(
        item.get("check_id") == "customer_approval_reference"
        and item.get("required") is True
        for item in checklist
    )


def _source_refs(
    readiness: dict[str, Any],
    operational: dict[str, Any],
) -> list[str]:
    return _unique_strings(
        [
            readiness["artifact_id"],
            operational["artifact_id"],
            *readiness.get("source_refs", []),
            *operational.get("source_refs", []),
        ]
    )


def _source_registry(
    readiness: dict[str, Any],
    operational: dict[str, Any],
) -> list[dict[str, str]]:
    registry = [
        {
            "artifact_id": readiness["artifact_id"],
            "path": (
                "experiments/results/r12_customer_trial_readiness_package/"
                "r12-customer-trial-readiness-package-current-001.json"
            ),
        },
        {
            "artifact_id": operational["artifact_id"],
            "path": (
                "experiments/results/r12_customer_trial_operational_check/"
                "r12-customer-trial-operational-check-current-001.json"
            ),
        },
    ]
    for entry in [
        *readiness.get("source_registry", []),
        *operational.get("source_registry", []),
    ]:
        if entry not in registry:
            registry.append(entry)
    return registry


def _unique_strings(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument(
        "--r12-customer-trial-readiness-package-path",
        required=True,
    )
    parser.add_argument(
        "--r12-customer-trial-operational-check-path",
        required=True,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_trial_launch_handoff_package(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        generated_at=args.generated_at,
        r12_customer_trial_readiness_package=load_json_artifact(
            args.r12_customer_trial_readiness_package_path
        ),
        r12_customer_trial_operational_check=load_json_artifact(
            args.r12_customer_trial_operational_check_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "launch_handoff_ready": artifact["acceptance_gates"][
                    "launch_handoff_package_ready"
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
