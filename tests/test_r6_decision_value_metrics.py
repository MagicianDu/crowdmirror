import json
import subprocess
import sys

from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics


def test_r6_decision_value_metrics_quantifies_recovery_and_false_alarms():
    report = build_r6_decision_value_metrics(
        artifact_id="r6-decision-value-metrics-test",
        run_id="r6-decision-value-metrics-run",
    )

    assert report["schema_version"] == "r6-decision-value-metrics-v1"
    assert report["status"] == "decision_value_partial_high_false_alarm"
    assert report["decision_value_passed"] is False
    assert report["summary"] == {
        "case_count": 3,
        "interaction_flagged_case_count": 3,
        "interaction_flagged_observed_high_risk_count": 1,
        "static_prior_miss_count": 1,
        "static_prior_miss_recovered_count": 1,
        "false_alarm_count": 2,
        "static_prior_miss_recovery_rate": 1.0,
        "top_k_risk_hit_rate": 0.333,
        "false_alarm_rate": 0.667,
        "decision_regret_reduction": 1,
    }
    by_source = {case["source_key"]: case for case in report["case_results"]}
    assert by_source["htops_cost_pressure"]["static_prior_missed_high_risk"] is True
    assert by_source["htops_cost_pressure"]["recovered_static_prior_miss"] is True
    assert by_source["anes_health_heldout"]["interaction_false_alarm"] is True
    assert by_source["anes_climate_heldout"]["interaction_false_alarm"] is True
    assert report["acceptance_gates"] == {
        "decision_value_metric_present": True,
        "static_prior_miss_recovery_observed": True,
        "top_k_risk_hit_rate_passed": False,
        "false_alarm_rate_passed": False,
        "decision_regret_reduction_positive": True,
        "decision_value_passed": False,
    }
    assert "needs_lower_false_alarm_rate" in report["blocking_gaps"]
    assert "needs_risk_discovery_holdout_validation" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_decision_value_metrics_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-decision-value-metrics.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_decision_value_metrics.py",
            "--artifact-id",
            "r6-decision-value-metrics-cli",
            "--run-id",
            "r6-decision-value-metrics-run",
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
    assert report["schema_version"] == "r6-decision-value-metrics-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-decision-value-metrics-cli",
        "decision_value_passed": False,
        "output": str(output),
        "status": "decision_value_partial_high_false_alarm",
    }
