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
from experiments.r12_customer_trial_readiness_package import (
    R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION,
)


R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION = (
    "r12-customer-trial-operational-check-v1"
)


def build_r12_customer_trial_operational_check(
    *,
    artifact_id: str,
    run_id: str,
    checked_at: str,
    r12_customer_trial_readiness_package: dict[str, Any],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    checked_at = non_empty_string(checked_at, field="checked_at")
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    _validate_trial_package(r12_customer_trial_readiness_package)

    package = r12_customer_trial_readiness_package
    trial_summary = package["trial_readiness_summary"]
    required_fields = _required_fields_from_checklist(package["customer_trial_checklist"])
    template_path = non_empty_string(
        trial_summary["template_output_path"],
        field="trial_readiness_summary.template_output_path",
    )
    template_resolved = _resolve_path(template_path, root)
    template_header = _template_header(template_resolved) if template_resolved.exists() else []
    missing_required_fields = [
        field for field in required_fields if field not in set(template_header)
    ]

    source_checks = _source_checks(package["source_registry"], root)
    unresolved_sources = [
        item for item in source_checks if item["path_resolvable"] is False
    ]
    command_checks = _operator_command_checks(package["operator_runbook"])
    operator_runbook_declared = bool(command_checks) and all(
        item["command_declared"] for item in command_checks
    )
    template_required_fields_present = not missing_required_fields
    template_path_resolvable = template_resolved.exists()
    source_registry_resolvable = not unresolved_sources
    operationally_ready = (
        template_path_resolvable
        and template_required_fields_present
        and source_registry_resolvable
        and operator_runbook_declared
    )
    status = (
        "r12_customer_trial_operational_check_ready_source_pending"
        if operationally_ready
        else "r12_customer_trial_operational_check_blocked_operational_gap"
    )

    report = {
        "schema_version": R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": "operational_trial_readiness_verified_no_validation_claim",
        "operational_summary": {
            "checked_at": checked_at,
            "trial_package_artifact_id": package["artifact_id"],
            "current_stage": trial_summary["current_stage"],
            "next_action": trial_summary["next_action"],
            "template_path": template_path,
            "template_path_resolvable": template_path_resolvable,
            "template_required_fields_present": template_required_fields_present,
            "source_registry_entry_count": len(source_checks),
            "source_registry_resolvable_count": sum(
                1 for item in source_checks if item["path_resolvable"]
            ),
            "operator_command_count": len(command_checks),
            "manual_approval_point_count": len(
                package["operator_runbook"]["manual_approval_points"]
            ),
        },
        "template_check": {
            "required_fields": required_fields,
            "template_header_fields": template_header,
            "missing_required_fields": missing_required_fields,
        },
        "source_registry_check": source_checks,
        "unresolved_sources": unresolved_sources,
        "operator_command_check": command_checks,
        "acceptance_gates": {
            "trial_readiness_package_loaded": True,
            "template_path_resolvable": template_path_resolvable,
            "template_required_fields_present": template_required_fields_present,
            "source_registry_resolvable": source_registry_resolvable,
            "operator_runbook_declared": operator_runbook_declared,
            "customer_trial_request_operationally_ready": operationally_ready,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": package["next_required_artifact"],
        "source_refs": [
            package["artifact_id"],
            *package.get("source_refs", []),
        ],
        "source_registry": _source_registry(package),
        "allowed_claims": [
            (
                "Product can verify that the customer trial readiness package "
                "has resolvable sources, template fields, and operator commands."
            ),
            (
                "The operational check is ready for customer field-slice "
                "collection, but does not claim field validation."
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


def write_r12_customer_trial_operational_check(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_trial_operational_check(**kwargs),
    )


def _validate_trial_package(artifact: dict[str, Any]) -> None:
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


def _required_fields_from_checklist(checklist: list[dict[str, Any]]) -> list[str]:
    for item in checklist:
        if item.get("check_id") == "required_fields":
            fields = [
                field.strip()
                for field in str(item.get("source_field", "")).split(",")
                if field.strip()
            ]
            if fields:
                return fields
    raise ValueError("customer_trial_checklist missing required_fields source_field")


def _template_header(path: Path) -> list[str]:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def _source_checks(
    source_registry: list[dict[str, Any]],
    repo_root: Path,
) -> list[dict[str, Any]]:
    checks = []
    for entry in source_registry:
        artifact_id = non_empty_string(entry.get("artifact_id"), field="artifact_id")
        path = non_empty_string(entry.get("path"), field=f"{artifact_id}.path")
        resolved = _resolve_path(path, repo_root)
        checks.append(
            {
                "artifact_id": artifact_id,
                "path": path,
                "path_resolvable": resolved.exists(),
            }
        )
    return checks


def _operator_command_checks(runbook: dict[str, Any]) -> list[dict[str, Any]]:
    commands = runbook.get("commands_after_source_arrival", [])
    if not isinstance(commands, list):
        raise ValueError("operator_runbook.commands_after_source_arrival must be a list")
    checks = []
    for command in commands:
        step_id = non_empty_string(command.get("step_id"), field="step_id")
        command_text = non_empty_string(command.get("command"), field=f"{step_id}.command")
        checks.append(
            {
                "step_id": step_id,
                "command_declared": True,
                "command": command_text,
            }
        )
    return checks


def _source_registry(package: dict[str, Any]) -> list[dict[str, str]]:
    registry = [
        {
            "artifact_id": package["artifact_id"],
            "path": (
                "experiments/results/r12_customer_trial_readiness_package/"
                "r12-customer-trial-readiness-package-current-001.json"
            ),
        },
    ]
    for entry in package.get("source_registry", []):
        if entry not in registry:
            registry.append(entry)
    return registry


def _resolve_path(path: str | Path, repo_root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--checked-at", required=True)
    parser.add_argument(
        "--r12-customer-trial-readiness-package-path",
        required=True,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_trial_operational_check(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        checked_at=args.checked_at,
        r12_customer_trial_readiness_package=load_json_artifact(
            args.r12_customer_trial_readiness_package_path
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "operationally_ready": artifact["acceptance_gates"][
                    "customer_trial_request_operationally_ready"
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
