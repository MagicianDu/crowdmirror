import json
import subprocess
import sys

from experiments.r6_false_alarm_discriminator import (
    build_r6_false_alarm_discriminator,
)


def test_r6_false_alarm_discriminator_rejects_overfit_case_family_rules():
    report = build_r6_false_alarm_discriminator(
        artifact_id="r6-false-alarm-discriminator-test",
        run_id="r6-false-alarm-discriminator-run",
    )

    assert report["schema_version"] == "r6-false-alarm-discriminator-v1"
    assert report["status"] == "false_alarm_discriminator_diagnostic_only"
    assert report["summary"] == {
        "case_count": 3,
        "true_positive_count": 1,
        "false_alarm_count": 2,
        "candidate_count": 3,
        "current_proxy_separating_candidate_count": 3,
        "pre_outcome_safe_candidate_count": 2,
        "post_outcome_diagnostic_candidate_count": 1,
        "generalizable_candidate_count": 0,
        "accepted_candidate_count": 0,
    }
    by_id = {
        candidate["candidate_id"]: candidate
        for candidate in report["candidate_discriminators"]
    }
    assert by_id["target_case_family_gate"]["summary"] == {
        "predicted_risk_count": 1,
        "true_positive_kept_count": 1,
        "false_alarm_kept_count": 0,
        "false_alarm_rejected_count": 2,
        "static_prior_miss_recovery_rate": 1.0,
        "false_alarm_rate": 0.0,
    }
    assert by_id["target_case_family_gate"]["current_proxy_separates"] is True
    assert by_id["target_case_family_gate"]["pre_outcome_safe"] is True
    assert by_id["target_case_family_gate"]["generalizable_without_holdout"] is False
    assert by_id["target_case_family_gate"]["accepted"] is False
    assert by_id["target_case_family_gate"]["rejection_reason"] == (
        "case_family_memory_without_in_family_positive_holdout"
    )
    assert by_id["post_outcome_static_error_gate"]["uses_observed_outcome"] is True
    assert by_id["post_outcome_static_error_gate"]["pre_outcome_safe"] is False
    assert report["acceptance_gates"] == {
        "false_alarm_discriminator_present": True,
        "current_proxy_separation_found": True,
        "pre_outcome_safe_candidate_found": True,
        "in_family_positive_signal_available": False,
        "generalizable_discriminator_found": False,
        "false_alarm_discriminator_ready": False,
    }
    assert report["decision"] == {
        "decision": "continue_but_do_not_accept_discriminator",
        "false_alarm_discriminator_ready": False,
        "recommended_next_step": "add_in_family_positive_signal_or_external_holdout_before_runtime_gate",
    }
    assert "case_family_gate_overfit_risk" in report["risk_flags"]
    assert "no_in_family_positive_signal" in report["risk_flags"]
    assert "needs_generalizable_false_alarm_discriminator" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_false_alarm_discriminator_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-false-alarm-discriminator.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_false_alarm_discriminator.py",
            "--artifact-id",
            "r6-false-alarm-discriminator-cli",
            "--run-id",
            "r6-false-alarm-discriminator-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-false-alarm-discriminator-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-false-alarm-discriminator-cli",
        "false_alarm_discriminator_ready": False,
        "output": str(output),
        "status": "false_alarm_discriminator_diagnostic_only",
    }
