from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime
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


R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION = (
    "r12-customer-field-slice-intake-validation-v1"
)

DIRECT_PII_COLUMN_NAMES = {
    "address",
    "email",
    "full_name",
    "id_card",
    "name",
    "passport",
    "phone",
    "ssn",
}

EMAIL_VALUE_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def build_r12_customer_field_slice_intake_validation(
    *,
    artifact_id: str,
    run_id: str,
    r12_customer_field_slice_handoff_package: dict[str, Any],
    intake_checked_at: str,
    customer_field_slice_path: str | Path | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    intake_checked_at = non_empty_string(
        intake_checked_at,
        field="intake_checked_at",
    )
    _validate_l21_handoff(r12_customer_field_slice_handoff_package)

    handoff = r12_customer_field_slice_handoff_package
    contract = handoff["field_slice_contract"]
    validation = _validate_customer_field_slice(
        customer_field_slice_path=customer_field_slice_path,
        required_fields=contract["required_fields"],
        minimum_case_count=contract["minimum_case_count"],
    )
    ready_for_revalidation = (
        validation["customer_field_slice_submitted"]
        and validation["required_fields_present"]
        and validation["minimum_case_count_met"]
        and validation["customer_approval_present"]
        and not validation["direct_pii_detected"]
        and validation["numeric_fields_valid"]
        and validation["timestamps_valid"]
        and not validation["duplicate_case_ids"]
    )

    if ready_for_revalidation:
        status = (
            "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
        )
        claim_level = "customer_field_slice_intake_validated_no_metric_claim"
        acceptance_decision = (
            "accept_customer_field_slice_intake_enable_revalidation_not_product_default"
        )
        next_required_artifact = (
            "r12_pre_outcome_or_customer_field_outcome_revalidation_with_customer_slice"
        )
        allowed_claims = [
            (
                "Customer field slice passed contract, privacy, numeric, "
                "timestamp, and duplicate-case intake checks."
            ),
            (
                "The validated slice can be passed to outcome revalidation, "
                "while Product default remains blocked."
            ),
        ]
    elif validation["customer_field_slice_submitted"]:
        status = (
            "r12_customer_field_slice_intake_validation_blocked_contract_or_privacy"
        )
        claim_level = "customer_field_slice_intake_blocked"
        acceptance_decision = "reject_customer_field_slice_intake_keep_waiting"
        next_required_artifact = "corrected_customer_field_slice"
        allowed_claims = [
            (
                "Customer field slice was received but blocked by contract, "
                "privacy, numeric, timestamp, or duplicate-case checks."
            )
        ]
    else:
        status = "r12_customer_field_slice_intake_validation_pending_no_slice"
        claim_level = "customer_field_slice_intake_pending"
        acceptance_decision = "keep_waiting_for_customer_field_slice_submission"
        next_required_artifact = "customer_field_slice_submission"
        allowed_claims = [
            (
                "Customer field slice intake validator is ready, but no slice "
                "has been submitted."
            )
        ]

    report = {
        "schema_version": (
            R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "intake_summary": {
            "handoff_artifact_id": handoff["artifact_id"],
            "intake_checked_at": intake_checked_at,
            "slice_path": validation["slice_path"],
            "case_count": validation["case_count"],
            "minimum_case_count": contract["minimum_case_count"],
            "ready_for_revalidation": ready_for_revalidation,
        },
        "validation_summary": {
            "required_fields": contract["required_fields"],
            "present_fields": validation["present_fields"],
            "missing_required_fields": validation["missing_required_fields"],
            "required_fields_present": validation["required_fields_present"],
            "minimum_case_count_met": validation["minimum_case_count_met"],
            "customer_approval_present": validation["customer_approval_present"],
            "direct_pii_detected": validation["direct_pii_detected"],
            "direct_pii_columns": validation["direct_pii_columns"],
            "direct_pii_value_hits": validation["direct_pii_value_hits"],
            "numeric_fields_valid": validation["numeric_fields_valid"],
            "numeric_parse_errors": validation["numeric_parse_errors"],
            "timestamps_valid": validation["timestamps_valid"],
            "timestamp_parse_errors": validation["timestamp_parse_errors"],
            "duplicate_case_ids": validation["duplicate_case_ids"],
        },
        "validation_errors": validation["validation_errors"],
        "acceptance_gates": {
            "customer_field_slice_submitted": validation[
                "customer_field_slice_submitted"
            ],
            "schema_valid": validation["required_fields_present"],
            "minimum_case_count_met": validation["minimum_case_count_met"],
            "customer_approval_present": validation["customer_approval_present"],
            "privacy_valid": not validation["direct_pii_detected"],
            "numeric_fields_valid": validation["numeric_fields_valid"],
            "timestamps_valid": validation["timestamps_valid"],
            "duplicate_case_ids_absent": not validation["duplicate_case_ids"],
            "ready_for_revalidation": ready_for_revalidation,
            "metrics_computed": False,
            "field_outcome_validated": False,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": acceptance_decision,
        "next_required_artifact": next_required_artifact,
        "source_refs": [
            handoff["artifact_id"],
            *(
                [f"customer_field_slice:{validation['slice_path']}"]
                if validation["slice_path"]
                else []
            ),
        ],
        "source_registry": [
            {
                "artifact_id": handoff["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_slice_handoff_package/"
                    "r12-customer-field-slice-handoff-package-current-001.json"
                ),
            },
            *(
                [
                    {
                        "artifact_id": (
                            f"customer_field_slice:{validation['slice_path']}"
                        ),
                        "path": validation["slice_path"],
                    }
                ]
                if validation["slice_path"]
                else []
            ),
        ],
        "allowed_claims": allowed_claims,
        "blocked_claims": [
            *(
                ["ready_for_revalidation=true"]
                if not ready_for_revalidation
                else []
            ),
            "metrics_computed=true",
            "field_or_pre_outcome_revalidation_passed=true",
            "field_outcome_validated=true",
            "direct personal identifiers in customer slice",
            "manual prompt/persona patch from customer slice",
            "Product default can use customer field slice by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_field_slice_intake_validation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_field_slice_intake_validation(**kwargs),
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


def _validate_customer_field_slice(
    *,
    customer_field_slice_path: str | Path | None,
    required_fields: list[str],
    minimum_case_count: int,
) -> dict[str, Any]:
    if customer_field_slice_path is None:
        return _empty_validation(required_fields=required_fields)

    path = Path(customer_field_slice_path)
    rows = _read_customer_field_slice(path)
    present_fields = sorted(set(rows[0].keys()) if rows else set())
    missing_required_fields = [
        field for field in required_fields if field not in set(present_fields)
    ]
    customer_approval_present = bool(rows) and all(
        str(row.get("customer_approval_reference", "")).strip()
        for row in rows
    )
    duplicate_case_ids = _duplicate_case_ids(rows)
    direct_pii_columns = [
        field for field in present_fields if field.lower() in DIRECT_PII_COLUMN_NAMES
    ]
    direct_pii_value_hits = _direct_pii_value_hits(rows)
    numeric_parse_errors = _numeric_parse_errors(
        rows=rows,
        numeric_fields=["prediction_share_or_score", "observed_outcome"],
    )
    timestamp_parse_errors = _timestamp_parse_errors(
        rows=rows,
        timestamp_field="outcome_timestamp",
    )
    validation_errors = _validation_errors(
        case_count=len(rows),
        minimum_case_count=minimum_case_count,
        missing_required_fields=missing_required_fields,
        customer_approval_present=customer_approval_present,
        direct_pii_columns=direct_pii_columns,
        direct_pii_value_hits=direct_pii_value_hits,
        numeric_parse_errors=numeric_parse_errors,
        timestamp_parse_errors=timestamp_parse_errors,
        duplicate_case_ids=duplicate_case_ids,
    )
    return {
        "customer_field_slice_submitted": True,
        "slice_path": str(path),
        "case_count": len(rows),
        "present_fields": present_fields,
        "missing_required_fields": missing_required_fields,
        "required_fields_present": not missing_required_fields,
        "minimum_case_count_met": len(rows) >= minimum_case_count,
        "customer_approval_present": customer_approval_present,
        "direct_pii_detected": bool(direct_pii_columns or direct_pii_value_hits),
        "direct_pii_columns": direct_pii_columns,
        "direct_pii_value_hits": direct_pii_value_hits,
        "numeric_fields_valid": not numeric_parse_errors,
        "numeric_parse_errors": numeric_parse_errors,
        "timestamps_valid": not timestamp_parse_errors,
        "timestamp_parse_errors": timestamp_parse_errors,
        "duplicate_case_ids": duplicate_case_ids,
        "validation_errors": validation_errors,
    }


def _empty_validation(*, required_fields: list[str]) -> dict[str, Any]:
    return {
        "customer_field_slice_submitted": False,
        "slice_path": None,
        "case_count": 0,
        "present_fields": [],
        "missing_required_fields": required_fields,
        "required_fields_present": False,
        "minimum_case_count_met": False,
        "customer_approval_present": False,
        "direct_pii_detected": False,
        "direct_pii_columns": [],
        "direct_pii_value_hits": [],
        "numeric_fields_valid": False,
        "numeric_parse_errors": [],
        "timestamps_valid": False,
        "timestamp_parse_errors": [],
        "duplicate_case_ids": [],
        "validation_errors": [
            {
                "code": "customer_field_slice_not_submitted",
                "message": "No customer field slice path was provided.",
            }
        ],
    }


def _read_customer_field_slice(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".csv":
        with path.open(newline="") as fh:
            return [dict(row) for row in csv.DictReader(fh)]
    if path.suffix == ".jsonl":
        rows = []
        for line in path.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
    raise ValueError("customer field slice must be csv or jsonl")


def _duplicate_case_ids(rows: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        case_id = str(row.get("case_id", "")).strip()
        if not case_id:
            continue
        if case_id in seen:
            duplicates.add(case_id)
        seen.add(case_id)
    return sorted(duplicates)


def _direct_pii_value_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits = []
    for idx, row in enumerate(rows):
        for field, value in row.items():
            text = str(value)
            if EMAIL_VALUE_PATTERN.search(text):
                hits.append({"row_index": idx, "field": field, "pattern": "email"})
    return hits


def _numeric_parse_errors(
    *,
    rows: list[dict[str, Any]],
    numeric_fields: list[str],
) -> list[dict[str, Any]]:
    errors = []
    for idx, row in enumerate(rows):
        for field in numeric_fields:
            try:
                value = float(row.get(field, ""))
            except (TypeError, ValueError):
                errors.append({"row_index": idx, "field": field})
                continue
            if not math.isfinite(value):
                errors.append({"row_index": idx, "field": field})
    return errors


def _timestamp_parse_errors(
    *,
    rows: list[dict[str, Any]],
    timestamp_field: str,
) -> list[dict[str, Any]]:
    errors = []
    for idx, row in enumerate(rows):
        text = str(row.get(timestamp_field, "")).strip()
        try:
            datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            errors.append({"row_index": idx, "field": timestamp_field})
    return errors


def _validation_errors(
    *,
    case_count: int,
    minimum_case_count: int,
    missing_required_fields: list[str],
    customer_approval_present: bool,
    direct_pii_columns: list[str],
    direct_pii_value_hits: list[dict[str, Any]],
    numeric_parse_errors: list[dict[str, Any]],
    timestamp_parse_errors: list[dict[str, Any]],
    duplicate_case_ids: list[str],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if case_count < minimum_case_count:
        errors.append(
            {
                "code": "minimum_case_count_not_met",
                "message": (
                    f"case_count={case_count} is below minimum_case_count="
                    f"{minimum_case_count}."
                ),
            }
        )
    if missing_required_fields:
        errors.append(
            {
                "code": "missing_required_fields",
                "fields": missing_required_fields,
            }
        )
    if not customer_approval_present:
        errors.append({"code": "customer_approval_reference_missing"})
    if direct_pii_columns:
        errors.append(
            {
                "code": "direct_pii_columns_present",
                "fields": direct_pii_columns,
            }
        )
    if direct_pii_value_hits:
        errors.append(
            {
                "code": "direct_pii_values_present",
                "hits": direct_pii_value_hits,
            }
        )
    if numeric_parse_errors:
        errors.append(
            {
                "code": "numeric_field_parse_failed",
                "errors": numeric_parse_errors,
            }
        )
    if timestamp_parse_errors:
        errors.append(
            {
                "code": "timestamp_parse_failed",
                "errors": timestamp_parse_errors,
            }
        )
    if duplicate_case_ids:
        errors.append(
            {
                "code": "duplicate_case_id",
                "case_ids": duplicate_case_ids,
            }
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-customer-field-slice-handoff-package-path",
        required=True,
    )
    parser.add_argument("--intake-checked-at", required=True)
    parser.add_argument("--customer-field-slice-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_field_slice_intake_validation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_customer_field_slice_handoff_package=load_json_artifact(
            args.r12_customer_field_slice_handoff_package_path
        ),
        intake_checked_at=args.intake_checked_at,
        customer_field_slice_path=args.customer_field_slice_path,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "ready_for_revalidation": artifact["acceptance_gates"][
                    "ready_for_revalidation"
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
