import json
import subprocess
import sys

from experiments.r9_holdout_guard import build_r9_holdout_guard
from experiments.r9_synthetic_mechanism_lab import build_r9_synthetic_mechanism_lab


def test_r9_holdout_guard_checks_leave_one_perturbation_and_near_threshold():
    synthetic_lab = build_r9_synthetic_mechanism_lab(
        artifact_id="r9-synthetic-mechanism-lab-test",
        run_id="r9-task4-run",
    )
    guard = build_r9_holdout_guard(
        artifact_id="r9-holdout-guard-test",
        run_id="r9-task4-run",
        synthetic_mechanism_lab=synthetic_lab,
    )

    assert guard["schema_version"] == "r9-holdout-guard-v1"
    assert guard["status"] == "r9_holdout_guard_guarded_partial_blocked"
    assert guard["candidate_combination_id"] == "A+B+C"
    assert guard["guard_contract"] == {
        "checks_leave_one_case": True,
        "checks_perturbation": True,
        "checks_near_threshold_false_alarm": True,
        "checks_synthetic_mechanism_recovery": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert guard["summary"] == {
        "leave_one_case_pass_rate": 0.667,
        "perturbation_pass_rate": 0.8,
        "near_threshold_false_alarm_passed": False,
        "synthetic_mechanism_recovery_passed": True,
        "overall_holdout_guard_passed": False,
    }
    assert len(guard["leave_one_case_trials"]) == 3
    assert len(guard["perturbation_trials"]) == 5
    assert guard["near_threshold_false_alarm_trial"]["passed"] is False
    assert guard["acceptance_gates"]["holdout_guard_passed"] is False
    assert guard["acceptance_gates"]["field_outcome_validated"] is False
    assert guard["acceptance_gates"]["runtime_default_allowed"] is False
    assert "R9 validated" in guard["blocked_claims"]
    json.dumps(guard, allow_nan=False)


def test_r9_holdout_guard_preserves_success_signal_as_diagnostic_only():
    guard = build_r9_holdout_guard(
        artifact_id="r9-holdout-guard-test",
        run_id="r9-task4-run",
    )

    assert guard["research_decision"] == (
        "keep_r9_candidate_diagnostic_until_near_threshold_false_alarm_fixed"
    )
    assert guard["product_decision"] == {
        "display_level": "diagnostic_only",
        "may_show_success_signal": True,
        "may_claim_runtime_method": False,
        "may_claim_field_validation": False,
    }
    assert guard["failure_reasons"] == [
        "near_threshold_false_alarm_failed",
        "leave_one_case_not_fully_passed",
        "current_fixture_candidate_not_field_validated",
    ]
    assert guard["next_required_tasks"] == [
        "redesign_near_threshold_false_alarm_gate",
        "rerun_leave_one_case_after_false_alarm_fix",
        "then_ingest_r9_support_gate_into_product_report_as_guarded_diagnostic",
    ]


def test_r9_holdout_guard_cli_writes_artifact(tmp_path):
    output = tmp_path / "r9-holdout-guard.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r9_holdout_guard.py",
            "--artifact-id",
            "r9-holdout-guard-cli",
            "--run-id",
            "r9-task4-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r9-holdout-guard-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r9-holdout-guard-cli",
        "output": str(output),
        "status": "r9_holdout_guard_guarded_partial_blocked",
    }
