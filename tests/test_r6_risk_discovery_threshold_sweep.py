import json
import subprocess
import sys

from experiments.r6_risk_discovery_threshold_sweep import (
    build_r6_risk_discovery_threshold_sweep,
)


def test_r6_risk_discovery_threshold_sweep_finds_no_separating_threshold():
    report = build_r6_risk_discovery_threshold_sweep(
        artifact_id="r6-risk-discovery-threshold-sweep-test",
        run_id="r6-risk-discovery-threshold-sweep-run",
        interaction_delta_thresholds=[0.0, 0.03, 0.07, 0.08],
    )

    assert report["schema_version"] == "r6-risk-discovery-threshold-sweep-v1"
    assert report["status"] == "threshold_sweep_no_separating_rule"
    assert report["summary"] == {
        "threshold_count": 4,
        "passing_threshold_count": 0,
        "separating_threshold_found": False,
        "false_alarm_reducible_by_threshold": False,
        "best_threshold": 0.0,
        "best_threshold_status": "decision_value_partial_high_false_alarm",
        "best_threshold_score": 1.666,
        "unique_interaction_delta_values": [0.07],
        "true_positive_delta_values": [0.07],
        "false_alarm_delta_values": [0.07],
        "true_signal_false_alarm_delta_overlap": True,
    }
    assert report["threshold_results"][0]["threshold"] == 0.0
    assert report["threshold_results"][0]["summary"]["false_alarm_rate"] == 0.667
    assert report["threshold_results"][-1]["threshold"] == 0.08
    assert report["threshold_results"][-1]["summary"][
        "static_prior_miss_recovery_rate"
    ] == 0.0
    assert report["acceptance_gates"] == {
        "threshold_sweep_present": True,
        "passing_threshold_found": False,
        "separating_threshold_found": False,
        "false_alarm_reducible_by_threshold": False,
        "true_signal_false_alarm_delta_overlap": True,
    }
    assert report["decision"] == {
        "threshold_tuning_sufficient": False,
        "decision": "needs_non_threshold_false_alarm_discriminator",
        "recommended_next_step": (
            "add_case_level_features_or_in_condition_holdout_before_threshold_tuning"
        ),
    }
    assert "threshold_tuning_cannot_resolve_current_false_alarms" in report[
        "risk_flags"
    ]
    json.dumps(report, allow_nan=False)


def test_r6_risk_discovery_threshold_sweep_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-risk-discovery-threshold-sweep.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_risk_discovery_threshold_sweep.py",
            "--artifact-id",
            "r6-risk-discovery-threshold-sweep-cli",
            "--run-id",
            "r6-risk-discovery-threshold-sweep-run",
            "--output",
            str(output),
            "--interaction-delta-threshold",
            "0.0",
            "--interaction-delta-threshold",
            "0.03",
            "--interaction-delta-threshold",
            "0.07",
            "--interaction-delta-threshold",
            "0.08",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-risk-discovery-threshold-sweep-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-risk-discovery-threshold-sweep-cli",
        "output": str(output),
        "passing_threshold_found": False,
        "status": "threshold_sweep_no_separating_rule",
    }
