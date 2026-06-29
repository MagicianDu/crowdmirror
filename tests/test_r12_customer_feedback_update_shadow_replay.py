import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_feedback_update_shadow_replay import (
    R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION,
    build_r12_customer_feedback_update_shadow_replay,
    write_r12_customer_feedback_update_shadow_replay,
)
from experiments.r12_customer_field_outcome_feedback_update import (
    build_r12_customer_field_outcome_feedback_update,
)
from experiments.r12_customer_field_slice_intake_validation import (
    build_r12_customer_field_slice_intake_validation,
)
from experiments.r12_customer_field_slice_revalidation import (
    build_r12_customer_field_slice_revalidation,
)


def test_r12_customer_feedback_update_shadow_replay_blocks_without_candidates():
    report = build_r12_customer_feedback_update_shadow_replay(
        artifact_id="r12-customer-feedback-update-shadow-replay-test",
        run_id="r12-l25-test",
        r12_customer_field_outcome_feedback_update=_load_current_l24(),
        replay_requested_at="2026-06-28T10:30:00Z",
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_feedback_update_shadow_replay_blocked_no_candidates"
    )
    assert report["claim_level"] == "customer_feedback_shadow_replay_blocked"
    assert report["shadow_replay_summary"] == {
        "feedback_update_artifact_id": (
            "r12-customer-field-outcome-feedback-update-current-001"
        ),
        "replay_requested_at": "2026-06-28T10:30:00Z",
        "candidate_count": 0,
        "replay_executed": False,
        "accepted_candidate_count": 0,
        "rejected_candidate_count": 0,
    }
    assert report["candidate_replay_results"] == []
    assert report["acceptance_gates"] == {
        "feedback_candidates_present": False,
        "shadow_replay_executed": False,
        "at_least_one_candidate_passed": False,
        "false_alarm_non_regression": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "shadow_replay_executed=true" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_feedback_update_shadow_replay_scores_bounded_candidates(
    tmp_path,
):
    feedback = _build_valid_feedback_update(tmp_path)

    report = build_r12_customer_feedback_update_shadow_replay(
        artifact_id="r12-customer-feedback-update-shadow-replay-test",
        run_id="r12-l25-test",
        r12_customer_field_outcome_feedback_update=feedback,
        replay_requested_at="2026-06-28T10:30:00Z",
    )

    assert report["status"] == (
        "r12_customer_feedback_update_shadow_replay_ready_guarded"
    )
    assert report["claim_level"] == (
        "customer_feedback_shadow_replay_candidates_no_product_default"
    )
    assert report["shadow_replay_summary"] == {
        "feedback_update_artifact_id": (
            "r12-customer-field-outcome-feedback-update-test"
        ),
        "replay_requested_at": "2026-06-28T10:30:00Z",
        "candidate_count": 2,
        "replay_executed": True,
        "accepted_candidate_count": 2,
        "rejected_candidate_count": 0,
    }
    assert report["candidate_replay_results"] == [
        {
            "candidate_id": "field-feedback-risk-pressure-increase-001",
            "update_target": "risk_pressure_multiplier",
            "update_direction": "increase",
            "replay_decision": "accepted_shadow_replay_candidate",
            "mean_absolute_error_delta": -0.01,
            "mean_signed_error_after": -0.01,
            "risk_ranking_quality_delta": 0.0,
            "false_alarm_regression_detected": False,
            "product_default_allowed": False,
        },
        {
            "candidate_id": "field-feedback-ranking-preserve-001",
            "update_target": "risk_ranking_operator",
            "update_direction": "preserve",
            "replay_decision": "accepted_shadow_replay_candidate",
            "mean_absolute_error_delta": 0.0,
            "mean_signed_error_after": -0.02,
            "risk_ranking_quality_delta": 0.0,
            "false_alarm_regression_detected": False,
            "product_default_allowed": False,
        },
    ]
    assert report["acceptance_gates"] == {
        "feedback_candidates_present": True,
        "shadow_replay_executed": True,
        "at_least_one_candidate_passed": True,
        "false_alarm_non_regression": True,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "Product default can use customer feedback shadow replay by default" in report[
        "blocked_claims"
    ]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_feedback_update_shadow_replay_writer_and_cli(tmp_path):
    feedback_path = tmp_path / "feedback-update.json"
    output = tmp_path / "shadow-replay.json"
    feedback_path.write_text(json.dumps(_load_current_l24(), allow_nan=False))

    output_path = write_r12_customer_feedback_update_shadow_replay(
        output=output,
        artifact_id="r12-customer-feedback-update-shadow-replay-test",
        run_id="r12-l25-test",
        r12_customer_field_outcome_feedback_update=_load_current_l24(),
        replay_requested_at="2026-06-28T10:30:00Z",
    )
    assert output_path == output
    assert json.loads(output.read_text())["shadow_replay_summary"][
        "replay_executed"
    ] is False

    cli_output = tmp_path / "shadow-replay-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_feedback_update_shadow_replay.py",
            "--artifact-id",
            "r12-customer-feedback-update-shadow-replay-cli",
            "--run-id",
            "r12-l25-cli-test",
            "--r12-customer-field-outcome-feedback-update-path",
            str(feedback_path),
            "--replay-requested-at",
            "2026-06-28T10:30:00Z",
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
        "r12-customer-feedback-update-shadow-replay-v1"
    )
    assert json.loads(completed.stdout) == {
        "accepted_candidate_count": 0,
        "artifact_id": "r12-customer-feedback-update-shadow-replay-cli",
        "output": str(cli_output),
        "replay_executed": False,
        "status": (
            "r12_customer_feedback_update_shadow_replay_blocked_no_candidates"
        ),
    }


def _build_valid_feedback_update(tmp_path: Path) -> dict:
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
    return build_r12_customer_field_outcome_feedback_update(
        artifact_id="r12-customer-field-outcome-feedback-update-test",
        run_id="r12-l24-test",
        r12_customer_field_slice_revalidation=revalidation,
        feedback_generated_at="2026-06-28T10:00:00Z",
    )


def _write_customer_slice(path: Path) -> None:
    fields = [
        "case_id",
        "segment_id",
        "scenario_id",
        "prediction_share_or_score",
        "observed_outcome",
        "outcome_timestamp",
        "customer_approval_reference",
    ]
    rows = [
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
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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


def _load_current_l24():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_field_outcome_feedback_update/"
            "r12-customer-field-outcome-feedback-update-current-001.json"
        ).read_text()
    )
