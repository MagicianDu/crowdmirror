import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_feedback_loop_operator_rehearsal import (
    R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION,
    build_r12_customer_feedback_loop_operator_rehearsal,
    write_r12_customer_feedback_loop_operator_rehearsal,
)


def test_r12_customer_feedback_loop_operator_rehearsal_runs_l22_to_l26_without_real_field_claim(
    tmp_path,
):
    work_dir = tmp_path / "feedback-loop-rehearsal"

    report = build_r12_customer_feedback_loop_operator_rehearsal(
        artifact_id="r12-customer-feedback-loop-operator-rehearsal-test",
        run_id="r12-l35-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_handoff_package_path=_current_l21_path(),
        rehearsal_started_at="2026-06-28T12:20:00Z",
        rehearsal_work_dir=work_dir,
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_feedback_loop_operator_rehearsal_ready_no_field_claim"
    )
    assert report["claim_level"] == (
        "synthetic_feedback_loop_rehearsal_only_no_customer_validation_claim"
    )
    assert report["rehearsal_summary"] == {
        "handoff_artifact_id": "r12-customer-field-slice-handoff-package-current-001",
        "rehearsal_started_at": "2026-06-28T12:20:00Z",
        "sample_slice_kind": "synthetic_feedback_loop_rehearsal_fixture",
        "sample_slice_path": str(
            work_dir / "r12-customer-feedback-loop-rehearsal-sample.csv"
        ),
        "case_count": 10,
        "required_field_count": 7,
        "intake_ready_for_revalidation": True,
        "synthetic_metrics_computed": True,
        "synthetic_field_metrics_passed": True,
        "feedback_candidate_count": 2,
        "shadow_replay_executed": True,
        "accepted_shadow_candidate_count": 2,
        "synthetic_holdout_review_executed": True,
        "synthetic_holdout_review_passed": True,
    }
    assert report["pipeline_artifacts"] == {
        "intake_validation": {
            "artifact_id": "r12-customer-field-slice-intake-validation-feedback-loop-rehearsal",
            "status": (
                "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
            ),
            "output_path": str(
                work_dir
                / "r12-customer-field-slice-intake-validation-feedback-loop-rehearsal.json"
            ),
        },
        "field_revalidation": {
            "artifact_id": "r12-customer-field-slice-revalidation-feedback-loop-rehearsal",
            "status": "r12_customer_field_slice_revalidation_metrics_ready_guarded",
            "output_path": str(
                work_dir
                / "r12-customer-field-slice-revalidation-feedback-loop-rehearsal.json"
            ),
        },
        "feedback_update": {
            "artifact_id": (
                "r12-customer-field-outcome-feedback-update-feedback-loop-rehearsal"
            ),
            "status": (
                "r12_customer_field_outcome_feedback_update_candidates_ready_guarded"
            ),
            "output_path": str(
                work_dir
                / "r12-customer-field-outcome-feedback-update-feedback-loop-rehearsal.json"
            ),
        },
        "shadow_replay": {
            "artifact_id": (
                "r12-customer-feedback-update-shadow-replay-feedback-loop-rehearsal"
            ),
            "status": "r12_customer_feedback_update_shadow_replay_ready_guarded",
            "output_path": str(
                work_dir
                / "r12-customer-feedback-update-shadow-replay-feedback-loop-rehearsal.json"
            ),
        },
        "holdout_review": {
            "artifact_id": (
                "r12-customer-feedback-shadow-replay-holdout-review-feedback-loop-rehearsal"
            ),
            "status": (
                "r12_customer_feedback_shadow_replay_holdout_review_ready_guarded"
            ),
            "output_path": str(
                work_dir
                / "r12-customer-feedback-shadow-replay-holdout-review-feedback-loop-rehearsal.json"
            ),
        },
    }
    for artifact in report["pipeline_artifacts"].values():
        assert Path(artifact["output_path"]).exists()
    assert report["acceptance_gates"] == {
        "synthetic_rehearsal_fixture_generated": True,
        "l22_intake_validator_executed": True,
        "l23_field_revalidation_executed": True,
        "l24_feedback_candidates_generated": True,
        "l25_shadow_replay_executed": True,
        "l26_synthetic_holdout_review_executed": True,
        "real_customer_field_slice_submitted": False,
        "real_independent_holdout_present": False,
        "field_outcome_validated": False,
        "metrics_computed_on_real_customer_slice": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "accept_feedback_loop_rehearsal_keep_customer_validation_blocked"
    )
    assert report["next_required_artifact"] == (
        "real_customer_field_slice_or_public_target_outcome"
    )
    assert "real_customer_field_slice_validated=true" in report["blocked_claims"]
    assert "field_outcome_validated=true" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_customer_feedback_loop_operator_rehearsal_writer_and_cli(tmp_path):
    handoff_path = tmp_path / "r12-l21.json"
    handoff_path.write_text(json.dumps(_load_current_l21(), allow_nan=False))
    output = tmp_path / "feedback-loop-rehearsal.json"
    work_dir = tmp_path / "rehearsal-work"

    output_path = write_r12_customer_feedback_loop_operator_rehearsal(
        output=output,
        artifact_id="r12-customer-feedback-loop-operator-rehearsal-test",
        run_id="r12-l35-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_handoff_package_path=handoff_path,
        rehearsal_started_at="2026-06-28T12:20:00Z",
        rehearsal_work_dir=work_dir,
    )

    assert output_path == output
    assert json.loads(output.read_text())["acceptance_gates"][
        "l25_shadow_replay_executed"
    ] is True

    cli_output = tmp_path / "feedback-loop-rehearsal-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_feedback_loop_operator_rehearsal.py",
            "--artifact-id",
            "r12-customer-feedback-loop-operator-rehearsal-cli",
            "--run-id",
            "r12-l35-cli-test",
            "--r12-customer-field-slice-handoff-package-path",
            str(handoff_path),
            "--rehearsal-started-at",
            "2026-06-28T12:20:00Z",
            "--rehearsal-work-dir",
            str(work_dir / "cli"),
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
        "r12-customer-feedback-loop-operator-rehearsal-v1"
    )
    assert json.loads(completed.stdout) == {
        "accepted_shadow_candidate_count": 2,
        "artifact_id": "r12-customer-feedback-loop-operator-rehearsal-cli",
        "output": str(cli_output),
        "status": (
            "r12_customer_feedback_loop_operator_rehearsal_ready_no_field_claim"
        ),
        "synthetic_holdout_review_executed": True,
    }


def _load_current_l21():
    return json.loads(_current_l21_path().read_text())


def _current_l21_path() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    return (
        repo_root
        / "experiments/results/"
        "r12_customer_field_slice_handoff_package/"
        "r12-customer-field-slice-handoff-package-current-001.json"
    )
