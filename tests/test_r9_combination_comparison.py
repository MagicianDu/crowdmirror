import json
import subprocess
import sys

from experiments.r9_combination_comparison import (
    R9_COMPARISON_METHOD_IDS,
    R9_COMPARISON_METRIC_IDS,
    build_r9_combination_comparison,
)


def test_r9_combination_comparison_scores_baselines_and_all_r9_combinations():
    report = build_r9_combination_comparison(
        artifact_id="r9-combination-comparison-test",
        run_id="r9-task3-run",
    )

    assert report["schema_version"] == "r9-combination-comparison-v1"
    assert report["status"] == "r9_combination_comparison_guarded_current_fixture_signal"
    assert report["comparison_scope"] == {
        "baseline_count": 4,
        "r9_combination_count": 7,
        "method_count": 11,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["method_ids"] == R9_COMPARISON_METHOD_IDS
    assert set(report["method_metrics"]) == set(R9_COMPARISON_METHOD_IDS)
    for method_id, metrics in report["method_metrics"].items():
        assert set(metrics) == set(R9_COMPARISON_METRIC_IDS), method_id
        for value in metrics.values():
            assert isinstance(value, float)
            assert 0 <= value <= 1
    assert report["acceptance_gates"]["baseline_comparison_present"] is True
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    assert "R9 validated" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r9_combination_comparison_reports_winners_and_stop_loss_boundary():
    report = build_r9_combination_comparison(
        artifact_id="r9-combination-comparison-test",
        run_id="r9-task3-run",
    )

    assert set(report["winner_by_metric"]) == set(R9_COMPARISON_METRIC_IDS)
    assert report["winner_by_metric"]["risk_ranking_quality"]["method"] == "A+B+C"
    assert report["winner_by_metric"]["decision_value_score"]["method"] == "A+B+C"
    assert report["r9_success_signal"] == {
        "status": "guarded_current_fixture_candidate",
        "best_combination_id": "A+B+C",
        "metrics_beating_r7_v2": [
            "risk_ranking_quality",
            "decision_value_score",
        ],
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["stop_loss_recommendation"] == (
        "continue_to_holdout_and_synthetic_lab_guarded"
    )
    assert report["claim_level"] == "current_fixture_diagnostic_only"


def test_r9_combination_comparison_keeps_failed_combinations_visible():
    report = build_r9_combination_comparison(
        artifact_id="r9-combination-comparison-test",
        run_id="r9-task3-run",
    )

    combination_results = report["r9_combination_results"]
    assert [item["combination_id"] for item in combination_results] == [
        "A_only",
        "B_only",
        "C_only",
        "A+B",
        "A+C",
        "B+C",
        "A+B+C",
    ]
    failed = [
        item
        for item in combination_results
        if item["claim_status"] == "diagnostic_failed_or_partial"
    ]
    candidates = [
        item
        for item in combination_results
        if item["claim_status"] == "guarded_current_fixture_candidate"
    ]
    assert len(failed) >= 3
    assert [item["combination_id"] for item in candidates] == ["A+B+C"]
    for item in combination_results:
        assert item["failure_or_limit_reasons"]
        assert item["source_refs"]
        assert item["field_outcome_validated"] is False
        assert item["runtime_default_allowed"] is False


def test_r9_combination_comparison_cli_writes_artifact(tmp_path):
    output = tmp_path / "r9-combination-comparison.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r9_combination_comparison.py",
            "--artifact-id",
            "r9-combination-comparison-cli",
            "--run-id",
            "r9-task3-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r9-combination-comparison-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r9-combination-comparison-cli",
        "output": str(output),
        "status": "r9_combination_comparison_guarded_current_fixture_signal",
    }
