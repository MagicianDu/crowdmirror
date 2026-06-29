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
from experiments.r12_customer_field_slice_handoff_package import (
    R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_intake_validation import (
    write_r12_customer_field_slice_intake_validation,
)


R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION = (
    "r12-customer-field-slice-operator-rehearsal-v1"
)

R12_CUSTOMER_FIELD_SLICE_OPERATOR_COMMAND_TEMPLATE = " ".join(
    [
        ".venv/bin/python",
        "experiments/r12_customer_field_slice_intake_validation.py",
        "--artifact-id",
        "r12-customer-field-slice-intake-validation-customer-001",
        "--run-id",
        "r12-customer-field-slice-intake-customer-001",
        "--r12-customer-field-slice-handoff-package-path",
        (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-handoff-package-current-001.json"
        ),
        "--intake-checked-at",
        "CUSTOMER_FIELD_SLICE_INTAKE_TIMESTAMP",
        "--customer-field-slice-path",
        "CUSTOMER_FIELD_SLICE_PATH",
        "--output",
        (
            "experiments/results/r12_customer_field_slice_intake_validation/"
            "r12-customer-field-slice-intake-validation-customer-001.json"
        ),
    ]
)


def build_r12_customer_field_slice_operator_rehearsal(
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
    minimum_case_count = contract["minimum_case_count"]
    required_fields = contract["required_fields"]
    work_dir = Path(rehearsal_work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    sample_slice_path = work_dir / "r12-customer-field-slice-rehearsal-sample.csv"
    intake_output_path = (
        work_dir / "r12-customer-field-slice-intake-validation-rehearsal.json"
    )

    _write_synthetic_rehearsal_slice(
        path=sample_slice_path,
        required_fields=required_fields,
        case_count=minimum_case_count,
    )
    write_r12_customer_field_slice_intake_validation(
        output=intake_output_path,
        artifact_id="r12-customer-field-slice-intake-validation-rehearsal",
        run_id=f"{run_id}-intake",
        r12_customer_field_slice_handoff_package=handoff,
        intake_checked_at=rehearsal_started_at,
        customer_field_slice_path=sample_slice_path,
    )
    intake_artifact = load_json_artifact(intake_output_path)
    sample_ready = bool(
        intake_artifact["acceptance_gates"]["ready_for_revalidation"]
    )
    status = (
        "r12_customer_field_slice_operator_rehearsal_ready_no_field_claim"
        if sample_ready
        else "r12_customer_field_slice_operator_rehearsal_blocked"
    )

    report = {
        "schema_version": (
            R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": "operator_rehearsal_only_no_customer_validation_claim",
        "rehearsal_summary": {
            "handoff_artifact_id": handoff["artifact_id"],
            "rehearsal_started_at": rehearsal_started_at,
            "sample_slice_kind": "synthetic_rehearsal_fixture",
            "sample_slice_path": str(sample_slice_path),
            "intake_output_path": str(intake_output_path),
            "case_count": minimum_case_count,
            "minimum_case_count": minimum_case_count,
            "required_field_count": len(required_fields),
            "operator_command_template_matches_demo": True,
            "intake_status": intake_artifact["status"],
            "sample_slice_ready_for_revalidation": sample_ready,
        },
        "operator_command_template": (
            R12_CUSTOMER_FIELD_SLICE_OPERATOR_COMMAND_TEMPLATE
        ),
        "intake_artifact_summary": {
            "artifact_id": intake_artifact["artifact_id"],
            "status": intake_artifact["status"],
            "ready_for_revalidation": sample_ready,
            "validation_errors": intake_artifact["validation_errors"],
        },
        "acceptance_gates": {
            "synthetic_rehearsal_fixture_generated": sample_slice_path.exists(),
            "operator_command_rehearsed": sample_ready,
            "intake_validator_executed": intake_output_path.exists(),
            "sample_slice_intake_ready_for_revalidation": sample_ready,
            "real_customer_field_slice_submitted": False,
            "metrics_computed": False,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": (
            "accept_operator_rehearsal_keep_customer_validation_blocked"
            if sample_ready
            else "reject_operator_rehearsal_fix_fixture_or_validator"
        ),
        "next_required_artifact": (
            "real_customer_field_slice_intake_validation_or_target_outcome_revalidation"
        ),
        "source_refs": [
            handoff["artifact_id"],
            intake_artifact["artifact_id"],
            f"synthetic_rehearsal_slice:{sample_slice_path}",
        ],
        "source_registry": [
            {
                "artifact_id": handoff["artifact_id"],
                "path": handoff_path,
            },
            {
                "artifact_id": intake_artifact["artifact_id"],
                "path": str(intake_output_path),
            },
            {
                "artifact_id": f"synthetic_rehearsal_slice:{sample_slice_path}",
                "path": str(sample_slice_path),
            },
        ],
        "allowed_claims": [
            (
                "An operator can run the customer field slice intake command "
                "shape on a synthetic rehearsal fixture."
            ),
            (
                "The rehearsal exercises the real L22 intake validator and "
                "keeps Product validation and runtime-default claims blocked."
            ),
        ],
        "blocked_claims": [
            "real_customer_field_slice_validated=true",
            "metrics_computed=true",
            "field_outcome_validated=true",
            "field_or_pre_outcome_revalidation_passed=true",
            "Product default can use customer field slice by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_field_slice_operator_rehearsal(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_field_slice_operator_rehearsal(**kwargs),
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


def _write_synthetic_rehearsal_slice(
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
    values = {
        "case_id": f"rehearsal-case-{idx:03d}",
        "segment_id": f"segment-{idx % 3}",
        "scenario_id": "scenario-rehearsal-001",
        "prediction_share_or_score": f"{0.10 + idx * 0.01:.3f}",
        "observed_outcome": f"{0.12 + idx * 0.01:.3f}",
        "outcome_timestamp": "2026-07-15T00:00:00Z",
        "customer_approval_reference": "synthetic-rehearsal-approval",
    }
    return values.get(field, f"synthetic-{field}-{idx}")


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
    output_path = write_r12_customer_field_slice_operator_rehearsal(
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
                "artifact_id": artifact["artifact_id"],
                "operator_command_rehearsed": artifact["acceptance_gates"][
                    "operator_command_rehearsed"
                ],
                "output": str(output_path),
                "sample_slice_ready_for_revalidation": artifact[
                    "rehearsal_summary"
                ]["sample_slice_ready_for_revalidation"],
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
