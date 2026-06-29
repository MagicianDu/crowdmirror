import json
import subprocess
import sys

from experiments.r8_baseline_comparison import build_r8_baseline_comparison


def test_r8_baseline_comparison_includes_all_required_methods():
    report = build_r8_baseline_comparison(
        artifact_id="r8-baseline-comparison-test",
        run_id="r8-baseline-run",
    )

    assert report["schema_version"] == "r8-baseline-comparison-v1"
    assert report["status"] in {
        "r8_baseline_comparison_guarded_positive",
        "r8_baseline_comparison_diagnostic_or_stop_loss",
    }
    assert set(report["methods"]) == {
        "static_prior",
        "r6_learning_counterfactual",
        "r7_v2_guarded_mechanism_calibrated",
        "r8_main_learnable_mechanism",
        "hierarchical_interval_baseline",
        "agent_propagation_baseline",
    }
    assert "r7-effect-validation-v2" in report["baseline_policy"]["r7_v2_role"]
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    json.dumps(report, allow_nan=False)


def test_r8_baseline_comparison_reports_winners_and_claim_levels():
    report = build_r8_baseline_comparison(
        artifact_id="r8-baseline-comparison-test",
        run_id="r8-baseline-run",
    )

    for metric in [
        "trend_direction_accuracy",
        "interval_coverage",
        "false_alarm_rate",
        "static_prior_miss_recovery_rate",
        "risk_ranking_quality",
    ]:
        assert metric in report["winner_by_metric"]
        assert report["winner_by_metric"][metric]["method"] in report["methods"]
        assert report["claim_level_by_metric"][metric] in {
            "guarded_current_proxy",
            "diagnostic_only",
            "blocked",
        }

    assert report["stop_loss_recommendation"] in {
        "continue_to_holdout_validation",
        "keep_r8_as_diagnostic_asset",
        "stop_loss_r8_main_method",
    }


def test_r8_baseline_comparison_cli_writes_artifact(tmp_path):
    output = tmp_path / "r8-baseline-comparison.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_baseline_comparison.py",
            "--artifact-id",
            "r8-baseline-comparison-cli",
            "--run-id",
            "r8-baseline-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-baseline-comparison-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-baseline-comparison-cli",
        "output": str(output),
        "status": artifact["status"],
    }
