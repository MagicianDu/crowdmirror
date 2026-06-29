import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_feedback_shadow_replay_holdout_review import (
    R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION,
    build_r12_customer_feedback_shadow_replay_holdout_review,
    write_r12_customer_feedback_shadow_replay_holdout_review,
)
from experiments.r12_customer_feedback_update_shadow_replay import (
    build_r12_customer_feedback_update_shadow_replay,
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


def test_r12_customer_feedback_shadow_replay_holdout_review_blocks_without_shadow_candidates():
    report = build_r12_customer_feedback_shadow_replay_holdout_review(
        artifact_id="r12-customer-feedback-shadow-replay-holdout-review-test",
        run_id="r12-l26-test",
        r12_customer_feedback_update_shadow_replay=_load_current_l25(),
        holdout_review_requested_at="2026-06-28T11:00:00Z",
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_feedback_shadow_replay_holdout_review_blocked_no_shadow_candidates"
    )
    assert report["claim_level"] == "customer_feedback_holdout_review_blocked"
    assert report["holdout_review_summary"] == {
        "shadow_replay_artifact_id": (
            "r12-customer-feedback-update-shadow-replay-current-001"
        ),
        "holdout_review_requested_at": "2026-06-28T11:00:00Z",
        "accepted_shadow_candidate_count": 0,
        "independent_holdout_case_count": 0,
        "holdout_review_executed": False,
        "holdout_review_passed": False,
    }
    assert report["candidate_holdout_results"] == []
    assert report["acceptance_gates"] == {
        "accepted_shadow_candidates_present": False,
        "independent_holdout_present": False,
        "holdout_review_executed": False,
        "holdout_review_passed": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "holdout_review_executed=true" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_feedback_shadow_replay_holdout_review_blocks_without_independent_holdout(
    tmp_path,
):
    shadow_replay = _build_shadow_replay_with_candidates(tmp_path)

    report = build_r12_customer_feedback_shadow_replay_holdout_review(
        artifact_id="r12-customer-feedback-shadow-replay-holdout-review-test",
        run_id="r12-l26-test",
        r12_customer_feedback_update_shadow_replay=shadow_replay,
        holdout_review_requested_at="2026-06-28T11:00:00Z",
    )

    assert report["status"] == (
        "r12_customer_feedback_shadow_replay_holdout_review_blocked_no_independent_holdout"
    )
    assert report["holdout_review_summary"] == {
        "shadow_replay_artifact_id": (
            "r12-customer-feedback-update-shadow-replay-test"
        ),
        "holdout_review_requested_at": "2026-06-28T11:00:00Z",
        "accepted_shadow_candidate_count": 2,
        "independent_holdout_case_count": 0,
        "holdout_review_executed": False,
        "holdout_review_passed": False,
    }
    assert report["candidate_holdout_results"] == []
    assert report["acceptance_gates"][
        "accepted_shadow_candidates_present"
    ] is True
    assert report["acceptance_gates"]["independent_holdout_present"] is False
    assert "independent_holdout_present=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_feedback_shadow_replay_holdout_review_runs_guarded_holdout_review(
    tmp_path,
):
    shadow_replay = _build_shadow_replay_with_candidates(tmp_path)

    report = build_r12_customer_feedback_shadow_replay_holdout_review(
        artifact_id="r12-customer-feedback-shadow-replay-holdout-review-test",
        run_id="r12-l26-test",
        r12_customer_feedback_update_shadow_replay=shadow_replay,
        holdout_review_requested_at="2026-06-28T11:00:00Z",
        independent_holdout_source_id="customer-approved-field-holdout-001",
        independent_holdout_case_count=12,
    )

    assert report["status"] == (
        "r12_customer_feedback_shadow_replay_holdout_review_ready_guarded"
    )
    assert report["claim_level"] == (
        "customer_feedback_holdout_review_ready_no_product_default"
    )
    assert report["holdout_review_summary"] == {
        "shadow_replay_artifact_id": (
            "r12-customer-feedback-update-shadow-replay-test"
        ),
        "holdout_review_requested_at": "2026-06-28T11:00:00Z",
        "accepted_shadow_candidate_count": 2,
        "independent_holdout_case_count": 12,
        "holdout_review_executed": True,
        "holdout_review_passed": True,
    }
    assert report["candidate_holdout_results"] == [
        {
            "candidate_id": "field-feedback-risk-pressure-increase-001",
            "holdout_decision": "accepted_for_guarded_field_review",
            "holdout_source_id": "customer-approved-field-holdout-001",
            "mean_absolute_error_delta": -0.01,
            "false_alarm_regression_detected": False,
            "product_default_allowed": False,
        },
        {
            "candidate_id": "field-feedback-ranking-preserve-001",
            "holdout_decision": "accepted_for_guarded_field_review",
            "holdout_source_id": "customer-approved-field-holdout-001",
            "mean_absolute_error_delta": 0.0,
            "false_alarm_regression_detected": False,
            "product_default_allowed": False,
        },
    ]
    assert report["acceptance_gates"] == {
        "accepted_shadow_candidates_present": True,
        "independent_holdout_present": True,
        "holdout_review_executed": True,
        "holdout_review_passed": True,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert "Product default can use customer feedback holdout review by default" in report[
        "blocked_claims"
    ]
    json.dumps(report, allow_nan=False)


def test_r12_customer_feedback_shadow_replay_holdout_review_writer_and_cli(tmp_path):
    shadow_path = tmp_path / "shadow-replay.json"
    output = tmp_path / "holdout-review.json"
    shadow_path.write_text(json.dumps(_load_current_l25(), allow_nan=False))

    output_path = write_r12_customer_feedback_shadow_replay_holdout_review(
        output=output,
        artifact_id="r12-customer-feedback-shadow-replay-holdout-review-test",
        run_id="r12-l26-test",
        r12_customer_feedback_update_shadow_replay=_load_current_l25(),
        holdout_review_requested_at="2026-06-28T11:00:00Z",
    )
    assert output_path == output
    assert json.loads(output.read_text())["holdout_review_summary"][
        "holdout_review_executed"
    ] is False

    cli_output = tmp_path / "holdout-review-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_feedback_shadow_replay_holdout_review.py",
            "--artifact-id",
            "r12-customer-feedback-shadow-replay-holdout-review-cli",
            "--run-id",
            "r12-l26-cli-test",
            "--r12-customer-feedback-update-shadow-replay-path",
            str(shadow_path),
            "--holdout-review-requested-at",
            "2026-06-28T11:00:00Z",
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
        "r12-customer-feedback-shadow-replay-holdout-review-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": (
            "r12-customer-feedback-shadow-replay-holdout-review-cli"
        ),
        "holdout_review_executed": False,
        "holdout_review_passed": False,
        "output": str(cli_output),
        "status": (
            "r12_customer_feedback_shadow_replay_holdout_review_blocked_no_shadow_candidates"
        ),
    }


def _build_shadow_replay_with_candidates(tmp_path: Path) -> dict:
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
    feedback = build_r12_customer_field_outcome_feedback_update(
        artifact_id="r12-customer-field-outcome-feedback-update-test",
        run_id="r12-l24-test",
        r12_customer_field_slice_revalidation=revalidation,
        feedback_generated_at="2026-06-28T10:00:00Z",
    )
    return build_r12_customer_feedback_update_shadow_replay(
        artifact_id="r12-customer-feedback-update-shadow-replay-test",
        run_id="r12-l25-test",
        r12_customer_field_outcome_feedback_update=feedback,
        replay_requested_at="2026-06-28T10:30:00Z",
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


def _load_current_l25():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_feedback_update_shadow_replay/"
            "r12-customer-feedback-update-shadow-replay-current-001.json"
        ).read_text()
    )
