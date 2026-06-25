import json
import subprocess
import sys

from experiments.r7_effect_validation import build_r7_effect_validation


def test_r7_effect_validation_reports_current_signal_and_baseline_gaps():
    report = build_r7_effect_validation(
        artifact_id="r7-effect-validation-test",
        run_id="r7-effect-validation-run",
    )

    assert report["schema_version"] == "r7-effect-validation-v1"
    assert report["status"] == "r7_effect_validation_diagnostic_blocked"
    assert report["claim_status"] == "diagnostic_blocked"
    assert report["summary"]["case_count"] == 3
    assert report["summary"]["r7_rollout_count_per_case"] == 50
    assert report["summary"]["r7_trend_direction_accuracy"] == 0.667
    assert report["summary"]["r7_interval_coverage"] == 0.0
    assert report["summary"]["r7_false_alarm_rate"] == 1.0
    assert report["summary"]["r7_static_prior_miss_recovery_rate"] == 0.0
    assert report["summary"]["r7_mean_absolute_error"] > report["summary"][
        "r6_learning_counterfactual_mean_absolute_error"
    ]
    assert report["summary"]["r7_effect_positive_signal"] is False

    assert report["acceptance_gates"] == {
        "effect_validation_present": True,
        "r7_trend_not_worse_than_r6_raw": True,
        "r7_interval_coverage_improves": False,
        "r7_false_alarm_improves_vs_r6_raw": False,
        "r7_mean_error_improves_vs_r6_learning": False,
        "strategy_sandbox_present": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "r7_effect_positive_signal": False,
    }
    assert "needs_r7_uncertainty_calibration" in report["blocking_gaps"]
    assert "needs_r7_mechanism_sensitivity_rebalance" in report["blocking_gaps"]
    assert "needs_r7_false_alarm_reduction_before_product_core_claim" in report[
        "blocking_gaps"
    ]
    assert "精准预测系统" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r7_effect_validation_keeps_case_level_comparisons_auditable():
    report = build_r7_effect_validation(
        artifact_id="r7-effect-validation-test",
        run_id="r7-effect-validation-run",
    )

    by_source = {case["source_key"]: case for case in report["case_results"]}
    assert set(by_source) == {
        "htops_cost_pressure",
        "anes_health_heldout",
        "anes_climate_heldout",
    }

    htops = by_source["htops_cost_pressure"]
    assert htops["target_case_id"] == "generic-public-service-policy-change"
    assert htops["observed_high_risk"] is True
    assert htops["r7_flags_high_risk"] is False
    assert htops["r7_static_prior_miss_recovered"] is False

    health = by_source["anes_health_heldout"]
    assert health["target_case_id"] == "generic-rights-rule-change"
    assert health["observed_high_risk"] is False
    assert health["r7_flags_high_risk"] is True
    assert health["r7_false_alarm"] is True

    climate = by_source["anes_climate_heldout"]
    assert climate["r7_trend_direction_matches_outcome"] is False
    assert climate["r7_interval_contains_observed"] is False
    assert climate["r7_false_alarm"] is True

    for case in report["case_results"]:
        assert case["r7_source_artifact_id"]
        assert case["source_refs"]
        assert case["strategy_sandbox_top_policy"]["policy_id"]


def test_r7_effect_validation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r7-effect-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r7_effect_validation.py",
            "--artifact-id",
            "r7-effect-validation-cli",
            "--run-id",
            "r7-effect-validation-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r7-effect-validation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r7-effect-validation-cli",
        "output": str(output),
        "status": "r7_effect_validation_diagnostic_blocked",
    }
