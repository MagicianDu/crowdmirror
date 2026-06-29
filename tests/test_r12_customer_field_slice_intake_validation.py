import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_field_slice_intake_validation import (
    R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION,
    build_r12_customer_field_slice_intake_validation,
    write_r12_customer_field_slice_intake_validation,
)


def test_r12_customer_field_slice_intake_validation_accepts_valid_csv_and_keeps_runtime_blocked(
    tmp_path,
):
    customer_slice = tmp_path / "customer-field-slice.csv"
    _write_valid_customer_slice(customer_slice)

    report = build_r12_customer_field_slice_intake_validation(
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        intake_checked_at="2026-06-27T16:05:00Z",
        customer_field_slice_path=customer_slice,
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
    )
    assert report["claim_level"] == (
        "customer_field_slice_intake_validated_no_metric_claim"
    )
    assert report["intake_summary"] == {
        "handoff_artifact_id": "r12-customer-field-slice-handoff-package-current-001",
        "intake_checked_at": "2026-06-27T16:05:00Z",
        "slice_path": str(customer_slice),
        "case_count": 10,
        "minimum_case_count": 10,
        "ready_for_revalidation": True,
    }
    assert report["validation_summary"]["required_fields_present"] is True
    assert report["validation_summary"]["minimum_case_count_met"] is True
    assert report["validation_summary"]["customer_approval_present"] is True
    assert report["validation_summary"]["direct_pii_detected"] is False
    assert report["validation_summary"]["numeric_fields_valid"] is True
    assert report["validation_summary"]["timestamps_valid"] is True
    assert report["validation_summary"]["duplicate_case_ids"] == []
    assert report["validation_errors"] == []
    assert report["acceptance_gates"] == {
        "customer_field_slice_submitted": True,
        "schema_valid": True,
        "minimum_case_count_met": True,
        "customer_approval_present": True,
        "privacy_valid": True,
        "numeric_fields_valid": True,
        "timestamps_valid": True,
        "duplicate_case_ids_absent": True,
        "ready_for_revalidation": True,
        "metrics_computed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_customer_field_slice_intake_enable_revalidation_not_product_default"
    )
    assert report["next_required_artifact"] == (
        "r12_pre_outcome_or_customer_field_outcome_revalidation_with_customer_slice"
    )
    assert "metrics_computed=true" in report["blocked_claims"]
    assert "field_outcome_validated=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_field_slice_intake_validation_blocks_pii_bad_numeric_and_duplicates(
    tmp_path,
):
    customer_slice = tmp_path / "customer-field-slice-with-pii.csv"
    _write_invalid_customer_slice(customer_slice)

    report = build_r12_customer_field_slice_intake_validation(
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        intake_checked_at="2026-06-27T16:05:00Z",
        customer_field_slice_path=customer_slice,
    )

    assert report["status"] == (
        "r12_customer_field_slice_intake_validation_blocked_contract_or_privacy"
    )
    assert report["claim_level"] == "customer_field_slice_intake_blocked"
    assert report["intake_summary"]["ready_for_revalidation"] is False
    assert report["validation_summary"]["direct_pii_detected"] is True
    assert report["validation_summary"]["numeric_fields_valid"] is False
    assert report["validation_summary"]["timestamps_valid"] is False
    assert report["validation_summary"]["duplicate_case_ids"] == ["case-0"]
    assert report["acceptance_gates"]["ready_for_revalidation"] is False
    assert report["acceptance_gates"]["privacy_valid"] is False
    assert report["acceptance_gates"]["numeric_fields_valid"] is False
    assert report["acceptance_gates"]["timestamps_valid"] is False
    assert report["acceptance_gates"]["duplicate_case_ids_absent"] is False
    assert {
        error["code"]
        for error in report["validation_errors"]
    } >= {
        "direct_pii_columns_present",
        "numeric_field_parse_failed",
        "timestamp_parse_failed",
        "duplicate_case_id",
    }
    assert "direct personal identifiers in customer slice" in report[
        "blocked_claims"
    ]


def test_r12_customer_field_slice_intake_validation_writer_and_cli(tmp_path):
    handoff_path = tmp_path / "r12-l21.json"
    customer_slice = tmp_path / "customer-field-slice.jsonl"
    output = tmp_path / "intake.json"
    handoff_path.write_text(json.dumps(_load_current_l21(), allow_nan=False))
    _write_valid_customer_slice_jsonl(customer_slice)

    output_path = write_r12_customer_field_slice_intake_validation(
        output=output,
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        intake_checked_at="2026-06-27T16:05:00Z",
        customer_field_slice_path=customer_slice,
    )
    assert output_path == output
    assert json.loads(output.read_text())["status"] == (
        "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
    )

    cli_output = tmp_path / "intake-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_field_slice_intake_validation.py",
            "--artifact-id",
            "r12-customer-field-slice-intake-validation-cli",
            "--run-id",
            "r12-l22-cli-test",
            "--r12-customer-field-slice-handoff-package-path",
            str(handoff_path),
            "--intake-checked-at",
            "2026-06-27T16:05:00Z",
            "--customer-field-slice-path",
            str(customer_slice),
            "--output",
            str(cli_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(cli_output.read_text())
    assert artifact["schema_version"] == (
        "r12-customer-field-slice-intake-validation-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-field-slice-intake-validation-cli",
        "output": str(cli_output),
        "status": (
            "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
        ),
        "ready_for_revalidation": True,
    }


def _write_valid_customer_slice(path: Path) -> None:
    fields = _required_fields()
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for idx in range(10):
            writer.writerow(_valid_row(idx))


def _write_valid_customer_slice_jsonl(path: Path) -> None:
    path.write_text(
        "\n".join(json.dumps(_valid_row(idx), allow_nan=False) for idx in range(10))
    )


def _write_invalid_customer_slice(path: Path) -> None:
    fields = [*_required_fields(), "email"]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for idx in range(10):
            row = _valid_row(idx)
            row["email"] = f"user-{idx}@example.com"
            if idx == 1:
                row["case_id"] = "case-0"
            if idx == 2:
                row["prediction_share_or_score"] = "not-a-number"
            if idx == 3:
                row["outcome_timestamp"] = "not-a-timestamp"
            writer.writerow(row)


def _valid_row(idx: int) -> dict[str, str]:
    return {
        "case_id": f"case-{idx}",
        "segment_id": f"segment-{idx % 3}",
        "scenario_id": "scenario-001",
        "prediction_share_or_score": f"0.{idx + 1}",
        "observed_outcome": f"0.{idx + 2}",
        "outcome_timestamp": "2026-07-15T00:00:00Z",
        "customer_approval_reference": "approval-2026-06-27",
    }


def _required_fields() -> list[str]:
    return [
        "case_id",
        "segment_id",
        "scenario_id",
        "prediction_share_or_score",
        "observed_outcome",
        "outcome_timestamp",
        "customer_approval_reference",
    ]


def _load_current_l21():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-handoff-package-current-001.json"
        ).read_text()
    )
