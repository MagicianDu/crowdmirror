import json
import subprocess
import sys

from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


def test_r6_trend_interval_risk_metrics_reports_product_relevant_research_gates():
    report = build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-test",
        run_id="r6-trend-interval-risk-run",
    )

    assert report["schema_version"] == "r6-trend-interval-risk-metrics-v1"
    assert report["status"] == "trend_interval_risk_partial_high_false_alarm"
    assert report["research_supports_product_core_value"] is False
    assert report["summary"]["case_count"] == 3
    assert report["summary"]["trend_direction_accuracy"] == 0.667
    assert report["summary"]["interval_coverage"] == 0.667
    assert report["summary"]["risk_ranking_quality"] == 0.333
    assert report["summary"]["false_alarm_rate"] == 0.667
    assert report["acceptance_gates"] == {
        "trend_direction_metric_present": True,
        "interval_coverage_metric_present": True,
        "risk_ranking_metric_present": True,
        "abnormal_segment_metric_present": True,
        "trend_direction_passed": False,
        "interval_coverage_passed": False,
        "risk_ranking_passed": False,
        "false_alarm_control_passed": False,
        "research_supports_product_core_value": False,
    }
    assert "needs_lower_false_alarm_rate" in report["blocking_gaps"]
    assert "needs_independent_or_field_outcome_support" in report["blocking_gaps"]
    assert "精准预测系统" in report["blocked_claims"]
    assert "field validation 已完成" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r6_trend_interval_risk_metrics_case_results_include_intervals_and_segments():
    report = build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-test",
        run_id="r6-trend-interval-risk-run",
    )

    by_source = {case["source_key"]: case for case in report["case_results"]}
    htops = by_source["htops_cost_pressure"]
    assert htops["trend_direction"] == "risk_up"
    assert htops["trend_direction_matches_outcome"] is True
    assert htops["risk_interval"]["lower"] <= htops["observed_reject_proxy"]
    assert htops["risk_interval"]["upper"] >= htops["observed_reject_proxy"]
    assert htops["top_abnormal_segments"][0]["segment_id"]
    assert htops["top_abnormal_segments"][0]["delta_reject"] > 0


def test_r6_trend_interval_risk_metrics_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-trend-interval-risk-metrics.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_trend_interval_risk_metrics.py",
            "--artifact-id",
            "r6-trend-interval-risk-metrics-cli",
            "--run-id",
            "r6-trend-interval-risk-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-trend-interval-risk-metrics-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-trend-interval-risk-metrics-cli",
        "output": str(output),
        "status": "trend_interval_risk_partial_high_false_alarm",
        "research_supports_product_core_value": False,
    }
