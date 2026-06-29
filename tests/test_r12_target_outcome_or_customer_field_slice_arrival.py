import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_target_outcome_or_customer_field_slice_arrival import (
    R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION,
    build_r12_target_outcome_or_customer_field_slice_arrival,
)


def test_r12_target_outcome_or_customer_field_slice_arrival_records_pending_no_source():
    report = build_r12_target_outcome_or_customer_field_slice_arrival(
        artifact_id="r12-target-outcome-or-customer-field-slice-arrival-test",
        run_id="r12-l20-test",
        r12_pre_outcome_or_customer_field_outcome_revalidation=_load_current_l19(),
        arrival_checked_at="2026-06-27T15:30:00Z",
    )

    assert report["schema_version"] == (
        R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_target_outcome_or_customer_field_slice_arrival_pending_no_source"
    )
    assert report["claim_level"] == "outcome_source_arrival_pending"
    assert report["arrival_summary"] == {
        "revalidation_artifact_id": (
            "r12-pre-outcome-or-customer-field-outcome-revalidation-current-001"
        ),
        "target_outcome_period": "May 2026",
        "prediction_case_count": 14,
        "prediction_lock_timestamp": "2026-06-27T14:45:00Z",
        "arrival_checked_at": "2026-06-27T15:30:00Z",
        "target_outcome_artifact_path_provided": False,
        "customer_field_slice_path_provided": False,
        "validated_customer_field_case_count": 0,
    }
    assert report["public_target_outcome_availability"] == {
        "expected_public_report": (
            "July 2026 Air Travel Consumer Report (May 2026 Data)"
        ),
        "latest_available_report": (
            "June 2026 Air Travel Consumer Report (April 2026 Data)"
        ),
        "official_reports_index_url": (
            "https://www.transportation.gov/individuals/aviation-consumer-protection/air-travel-consumer-reports"
        ),
        "latest_news_url": "https://www.transportation.gov/airconsumer/latest-news",
        "target_report_found": False,
        "target_outcome_artifact_path": None,
    }
    assert report["customer_field_slice_validation"] == {
        "accepted_formats": ["csv", "jsonl"],
        "minimum_case_count": 10,
        "required_fields": [
            "case_id",
            "segment_id",
            "scenario_id",
            "prediction_share_or_score",
            "observed_outcome",
            "outcome_timestamp",
            "customer_approval_reference",
        ],
        "slice_path": None,
        "case_count": 0,
        "missing_required_fields": [],
        "customer_approval_present": False,
    }
    assert report["acceptance_gates"] == {
        "revalidation_harness_ready": True,
        "outcome_source_arrived": False,
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "metrics_computed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "keep_waiting_for_target_outcome_or_customer_field_slice"
    )
    assert report["next_required_artifact"] == (
        "r12_target_outcome_or_customer_field_slice_arrival"
    )
    assert "outcome_source_arrived=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_target_outcome_or_customer_field_slice_arrival_accepts_valid_customer_slice(
    tmp_path,
):
    customer_slice = tmp_path / "customer-field-slice.csv"
    _write_valid_customer_slice(customer_slice)

    report = build_r12_target_outcome_or_customer_field_slice_arrival(
        artifact_id="r12-target-outcome-or-customer-field-slice-arrival-test",
        run_id="r12-l20-customer-slice-test",
        r12_pre_outcome_or_customer_field_outcome_revalidation=_load_current_l19(),
        arrival_checked_at="2026-06-27T15:30:00Z",
        customer_field_slice_path=customer_slice,
    )

    assert report["status"] == (
        "r12_target_outcome_or_customer_field_slice_arrival_ready_customer_field_slice"
    )
    assert report["claim_level"] == (
        "customer_field_slice_arrived_revalidation_ready"
    )
    assert report["arrival_summary"][
        "customer_field_slice_path_provided"
    ] is True
    assert report["arrival_summary"][
        "validated_customer_field_case_count"
    ] == 10
    assert report["customer_field_slice_validation"]["slice_path"] == str(
        customer_slice
    )
    assert report["customer_field_slice_validation"]["case_count"] == 10
    assert report["customer_field_slice_validation"][
        "missing_required_fields"
    ] == []
    assert report["customer_field_slice_validation"][
        "customer_approval_present"
    ] is True
    assert report["acceptance_gates"] == {
        "revalidation_harness_ready": True,
        "outcome_source_arrived": True,
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": True,
        "customer_approval_present": True,
        "field_or_pre_outcome_revalidation_ready": True,
        "metrics_computed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_customer_field_slice_arrival_enable_revalidation_not_product_default"
    )
    assert report["next_required_artifact"] == (
        "r12_pre_outcome_or_customer_field_outcome_revalidation_with_arrived_outcome"
    )
    assert "Customer-approved field slice has arrived" in report[
        "allowed_claims"
    ][0]
    assert "metrics_computed=true" in report["blocked_claims"]


def test_r12_target_outcome_or_customer_field_slice_arrival_cli_writes_artifact(
    tmp_path,
):
    revalidation_path = tmp_path / "r12-l19.json"
    output = tmp_path / "r12-l20.json"
    revalidation_path.write_text(json.dumps(_load_current_l19(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_target_outcome_or_customer_field_slice_arrival.py",
            "--artifact-id",
            "r12-target-outcome-or-customer-field-slice-arrival-cli",
            "--run-id",
            "r12-l20-test",
            "--r12-pre-outcome-or-customer-field-outcome-revalidation-path",
            str(revalidation_path),
            "--arrival-checked-at",
            "2026-06-27T15:30:00Z",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == (
        "r12-target-outcome-or-customer-field-slice-arrival-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-target-outcome-or-customer-field-slice-arrival-cli",
        "output": str(output),
        "status": (
            "r12_target_outcome_or_customer_field_slice_arrival_pending_no_source"
        ),
    }


def _write_valid_customer_slice(path: Path) -> None:
    fields = [
        "case_id",
        "segment_id",
        "scenario_id",
        "prediction_share_or_score",
        "observed_outcome",
        "outcome_timestamp",
        "customer_approval_reference",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for idx in range(10):
            writer.writerow(
                {
                    "case_id": f"case-{idx}",
                    "segment_id": f"segment-{idx % 3}",
                    "scenario_id": "scenario-001",
                    "prediction_share_or_score": f"0.{idx + 1}",
                    "observed_outcome": f"0.{idx + 2}",
                    "outcome_timestamp": "2026-06-27T15:00:00Z",
                    "customer_approval_reference": "approval-2026-06-27",
                }
            )


def _load_current_l19():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_pre_outcome_or_customer_field_outcome_revalidation/"
            "r12-pre-outcome-or-customer-field-outcome-revalidation-current-001.json"
        ).read_text()
    )
