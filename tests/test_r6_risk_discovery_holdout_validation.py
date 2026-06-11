import json
import subprocess
import sys

from experiments.r6_risk_discovery_holdout_validation import (
    build_r6_risk_discovery_holdout_validation,
)


def test_r6_risk_discovery_holdout_validation_rejects_current_same_family_false_alarm():
    report = build_r6_risk_discovery_holdout_validation(
        artifact_id="r6-risk-discovery-holdout-validation-test",
        run_id="r6-risk-discovery-holdout-validation-run",
    )

    assert report["schema_version"] == "r6-risk-discovery-holdout-validation-v1"
    assert report["status"] == "risk_discovery_holdout_failed_current_public_proxies"
    assert report["acceptance_gates"] == {
        "risk_discovery_holdout_validation_present": True,
        "frozen_rule_has_no_holdout_outcome_leakage": True,
        "same_family_holdout_available": True,
        "positive_source_signal_available": False,
        "passed_same_family_holdout_count_positive": False,
        "risk_discovery_holdout_passed": False,
        "field_outcome_validated": False,
    }
    assert report["summary"] == {
        "trial_count": 2,
        "same_family_trial_count": 2,
        "passed_trial_count": 0,
        "failed_trial_count": 2,
        "condition_not_met_count": 2,
    }
    assert [
        (trial["trial_id"], trial["validation_status"])
        for trial in report["holdout_trials"]
    ] == [
        (
            "risk-discovery:anes_health_heldout->anes_climate_heldout",
            "source_signal_not_supported",
        ),
        (
            "risk-discovery:anes_climate_heldout->anes_health_heldout",
            "source_signal_not_supported",
        ),
    ]
    assert "needs_positive_same_family_source_signal" in report["blocking_gaps"]
    assert "needs_field_outcome_validation" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_risk_discovery_holdout_validation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-risk-discovery-holdout-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_risk_discovery_holdout_validation.py",
            "--artifact-id",
            "r6-risk-discovery-holdout-validation-cli",
            "--run-id",
            "r6-risk-discovery-holdout-validation-run",
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
    assert report["schema_version"] == "r6-risk-discovery-holdout-validation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-risk-discovery-holdout-validation-cli",
        "output": str(output),
        "risk_discovery_holdout_passed": False,
        "status": "risk_discovery_holdout_failed_current_public_proxies",
    }
