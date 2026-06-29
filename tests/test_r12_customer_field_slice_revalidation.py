import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_field_slice_intake_validation import (
    build_r12_customer_field_slice_intake_validation,
)
from experiments.r12_customer_field_slice_revalidation import (
    R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION,
    build_r12_customer_field_slice_revalidation,
    write_r12_customer_field_slice_revalidation,
)


def test_r12_customer_field_slice_revalidation_blocks_without_validated_intake():
    report = build_r12_customer_field_slice_revalidation(
        artifact_id="r12-customer-field-slice-revalidation-test",
        run_id="r12-l23-test",
        r12_customer_field_slice_intake_validation=_load_current_l22(),
        revalidation_checked_at="2026-06-28T09:15:00Z",
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_field_slice_revalidation_blocked_no_validated_intake"
    )
    assert report["claim_level"] == "customer_field_revalidation_blocked"
    assert report["revalidation_summary"] == {
        "intake_artifact_id": "r12-customer-field-slice-intake-validation-current-001",
        "revalidation_checked_at": "2026-06-28T09:15:00Z",
        "slice_path": None,
        "case_count": 0,
        "metrics_computed": False,
        "field_outcome_validated": False,
    }
    assert report["metric_results"] == {}
    assert report["acceptance_gates"] == {
        "validated_intake_ready": False,
        "customer_field_slice_present": False,
        "metrics_computed": False,
        "mae_threshold_passed": False,
        "risk_ranking_quality_threshold_passed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "field_outcome_validated=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_field_slice_revalidation_computes_metrics_from_validated_slice(
    tmp_path,
):
    customer_slice = tmp_path / "customer-field-slice.csv"
    _write_customer_slice(customer_slice)
    intake = build_r12_customer_field_slice_intake_validation(
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        intake_checked_at="2026-06-28T09:00:00Z",
        customer_field_slice_path=customer_slice,
    )

    report = build_r12_customer_field_slice_revalidation(
        artifact_id="r12-customer-field-slice-revalidation-test",
        run_id="r12-l23-test",
        r12_customer_field_slice_intake_validation=intake,
        revalidation_checked_at="2026-06-28T09:15:00Z",
        mae_threshold=0.05,
        risk_ranking_quality_threshold=0.8,
    )

    assert report["status"] == (
        "r12_customer_field_slice_revalidation_metrics_ready_guarded"
    )
    assert report["claim_level"] == (
        "customer_field_revalidation_metrics_ready_no_product_default"
    )
    assert report["revalidation_summary"] == {
        "intake_artifact_id": "r12-customer-field-slice-intake-validation-test",
        "revalidation_checked_at": "2026-06-28T09:15:00Z",
        "slice_path": str(customer_slice),
        "case_count": 10,
        "metrics_computed": True,
        "field_outcome_validated": True,
    }
    assert report["metric_results"] == {
        "mean_absolute_error": 0.02,
        "mean_signed_error": -0.02,
        "risk_ranking_quality": 1.0,
        "top_quintile_overlap": 1.0,
        "mae_threshold": 0.05,
        "risk_ranking_quality_threshold": 0.8,
    }
    assert report["acceptance_gates"] == {
        "validated_intake_ready": True,
        "customer_field_slice_present": True,
        "metrics_computed": True,
        "mae_threshold_passed": True,
        "risk_ranking_quality_threshold_passed": True,
        "field_outcome_validated": True,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_customer_field_revalidation_metrics_keep_product_default_blocked"
    )
    assert "Product default can use customer field validation by default" in report[
        "blocked_claims"
    ]


def test_r12_customer_field_slice_revalidation_writer_and_cli(tmp_path):
    customer_slice = tmp_path / "customer-field-slice.jsonl"
    intake_path = tmp_path / "intake.json"
    output = tmp_path / "revalidation.json"
    _write_customer_slice_jsonl(customer_slice)
    intake = build_r12_customer_field_slice_intake_validation(
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        intake_checked_at="2026-06-28T09:00:00Z",
        customer_field_slice_path=customer_slice,
    )
    intake_path.write_text(json.dumps(intake, allow_nan=False))

    output_path = write_r12_customer_field_slice_revalidation(
        output=output,
        artifact_id="r12-customer-field-slice-revalidation-test",
        run_id="r12-l23-test",
        r12_customer_field_slice_intake_validation=intake,
        revalidation_checked_at="2026-06-28T09:15:00Z",
    )
    assert output_path == output
    assert json.loads(output.read_text())["metric_results"][
        "risk_ranking_quality"
    ] == 1.0

    cli_output = tmp_path / "revalidation-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_field_slice_revalidation.py",
            "--artifact-id",
            "r12-customer-field-slice-revalidation-cli",
            "--run-id",
            "r12-l23-cli-test",
            "--r12-customer-field-slice-intake-validation-path",
            str(intake_path),
            "--revalidation-checked-at",
            "2026-06-28T09:15:00Z",
            "--output",
            str(cli_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(cli_output.read_text())
    assert artifact["schema_version"] == "r12-customer-field-slice-revalidation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-field-slice-revalidation-cli",
        "field_outcome_validated": True,
        "metrics_computed": True,
        "output": str(cli_output),
        "status": "r12_customer_field_slice_revalidation_metrics_ready_guarded",
    }


def _write_customer_slice(path: Path) -> None:
    fields = _required_fields()
    rows = _customer_rows()
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_customer_slice_jsonl(path: Path) -> None:
    path.write_text("\n".join(json.dumps(row, allow_nan=False) for row in _customer_rows()))


def _customer_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": f"case-{idx}",
            "segment_id": f"segment-{idx % 3}",
            "scenario_id": "scenario-001",
            "prediction_share_or_score": f"{0.10 + idx * 0.03:.3f}",
            "observed_outcome": f"{0.12 + idx * 0.03:.3f}",
            "outcome_timestamp": "2026-07-15T00:00:00Z",
            "customer_approval_reference": "approval-2026-06-28",
        }
        for idx in range(10)
    ]


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


def _load_current_l22():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_field_slice_intake_validation/"
            "r12-customer-field-slice-intake-validation-current-001.json"
        ).read_text()
    )
