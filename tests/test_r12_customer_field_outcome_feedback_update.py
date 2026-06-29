import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_field_outcome_feedback_update import (
    R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
    build_r12_customer_field_outcome_feedback_update,
    write_r12_customer_field_outcome_feedback_update,
)
from experiments.r12_customer_field_slice_intake_validation import (
    build_r12_customer_field_slice_intake_validation,
)
from experiments.r12_customer_field_slice_revalidation import (
    build_r12_customer_field_slice_revalidation,
)


def test_r12_customer_field_outcome_feedback_update_blocks_without_field_validation():
    report = build_r12_customer_field_outcome_feedback_update(
        artifact_id="r12-customer-field-outcome-feedback-update-test",
        run_id="r12-l24-test",
        r12_customer_field_slice_revalidation=_load_current_l23(),
        feedback_generated_at="2026-06-28T10:00:00Z",
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_field_outcome_feedback_update_blocked_no_field_validation"
    )
    assert report["claim_level"] == "customer_field_feedback_update_blocked"
    assert report["feedback_summary"] == {
        "revalidation_artifact_id": (
            "r12-customer-field-slice-revalidation-current-001"
        ),
        "feedback_generated_at": "2026-06-28T10:00:00Z",
        "metrics_consumed": False,
        "field_outcome_validated": False,
        "candidate_count": 0,
    }
    assert report["candidate_updates"] == []
    assert report["acceptance_gates"] == {
        "field_outcome_validated": False,
        "metrics_consumed": False,
        "candidate_updates_generated": False,
        "prompt_or_persona_manual_patch_allowed": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "candidate_updates_generated=true" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_field_outcome_feedback_update_generates_bounded_candidates(
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
    revalidation = build_r12_customer_field_slice_revalidation(
        artifact_id="r12-customer-field-slice-revalidation-test",
        run_id="r12-l23-test",
        r12_customer_field_slice_intake_validation=intake,
        revalidation_checked_at="2026-06-28T09:15:00Z",
    )

    report = build_r12_customer_field_outcome_feedback_update(
        artifact_id="r12-customer-field-outcome-feedback-update-test",
        run_id="r12-l24-test",
        r12_customer_field_slice_revalidation=revalidation,
        feedback_generated_at="2026-06-28T10:00:00Z",
    )

    assert report["status"] == (
        "r12_customer_field_outcome_feedback_update_candidates_ready_guarded"
    )
    assert report["claim_level"] == (
        "customer_field_feedback_update_candidates_no_product_default"
    )
    assert report["feedback_summary"] == {
        "revalidation_artifact_id": "r12-customer-field-slice-revalidation-test",
        "feedback_generated_at": "2026-06-28T10:00:00Z",
        "metrics_consumed": True,
        "field_outcome_validated": True,
        "candidate_count": 2,
    }
    assert report["metric_inputs"] == {
        "mean_absolute_error": 0.02,
        "mean_signed_error": -0.02,
        "risk_ranking_quality": 1.0,
        "top_quintile_overlap": 1.0,
    }
    assert report["candidate_updates"] == [
        {
            "candidate_id": "field-feedback-risk-pressure-increase-001",
            "update_target": "risk_pressure_multiplier",
            "update_direction": "increase",
            "rationale": (
                "Observed outcomes are higher than predictions; increase "
                "risk-pressure response in shadow review."
            ),
            "evidence_metric": "mean_signed_error",
            "evidence_value": -0.02,
            "review_status": "shadow_review_required",
            "product_default_allowed": False,
        },
        {
            "candidate_id": "field-feedback-ranking-preserve-001",
            "update_target": "risk_ranking_operator",
            "update_direction": "preserve",
            "rationale": (
                "Field ranking quality passed threshold; preserve ranking "
                "operator and focus calibration update on level bias."
            ),
            "evidence_metric": "risk_ranking_quality",
            "evidence_value": 1.0,
            "review_status": "shadow_review_required",
            "product_default_allowed": False,
        },
    ]
    assert report["acceptance_gates"] == {
        "field_outcome_validated": True,
        "metrics_consumed": True,
        "candidate_updates_generated": True,
        "prompt_or_persona_manual_patch_allowed": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "manual prompt/persona patch from customer feedback" in report[
        "blocked_claims"
    ]
    assert "Product default can use customer feedback update by default" in report[
        "blocked_claims"
    ]
    json.dumps(report, allow_nan=False)


def test_r12_customer_field_outcome_feedback_update_writer_and_cli(tmp_path):
    output = tmp_path / "feedback-update.json"
    revalidation_path = tmp_path / "revalidation.json"
    revalidation_path.write_text(json.dumps(_load_current_l23(), allow_nan=False))

    output_path = write_r12_customer_field_outcome_feedback_update(
        output=output,
        artifact_id="r12-customer-field-outcome-feedback-update-test",
        run_id="r12-l24-test",
        r12_customer_field_slice_revalidation=_load_current_l23(),
        feedback_generated_at="2026-06-28T10:00:00Z",
    )
    assert output_path == output
    assert json.loads(output.read_text())["feedback_summary"]["candidate_count"] == 0

    cli_output = tmp_path / "feedback-update-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_field_outcome_feedback_update.py",
            "--artifact-id",
            "r12-customer-field-outcome-feedback-update-cli",
            "--run-id",
            "r12-l24-cli-test",
            "--r12-customer-field-slice-revalidation-path",
            str(revalidation_path),
            "--feedback-generated-at",
            "2026-06-28T10:00:00Z",
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
        "r12-customer-field-outcome-feedback-update-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-field-outcome-feedback-update-cli",
        "candidate_count": 0,
        "metrics_consumed": False,
        "output": str(cli_output),
        "status": (
            "r12_customer_field_outcome_feedback_update_blocked_no_field_validation"
        ),
    }


def _write_customer_slice(path: Path) -> None:
    fields = _required_fields()
    rows = _customer_rows()
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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


def _load_current_l23():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_field_slice_revalidation/"
            "r12-customer-field-slice-revalidation-current-001.json"
        ).read_text()
    )
