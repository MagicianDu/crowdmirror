import json
import subprocess
import sys

import pytest

from experiments.r6_research_product_value_support import (
    build_r6_research_product_value_support,
)


def test_r6_research_product_value_support_maps_research_to_product_values():
    report = build_r6_research_product_value_support(
        artifact_id="r6-research-product-value-support-test",
        run_id="r6-product-value-run",
    )

    assert report["schema_version"] == "r6-research-product-value-support-v1"
    assert report["status"] == "product_value_support_partial"
    assert report["overall_product_core_value_supported"] is False
    support = {
        item["product_value"]: item["support_status"]
        for item in report["support_matrix"]
    }
    assert support == {
        "trend_direction": "partial_current_proxy",
        "risk_interval": "partial_current_proxy",
        "risk_distribution": "partial_high_false_alarm",
        "abnormal_segments": "diagnostic_only",
        "mechanism_explanation": "diagnostic_only",
        "outcome_feedback_learning": "blocked_until_holdout_or_field_outcome",
    }
    assert "needs_trend_interval_holdout_support" in report["blocking_gaps"]
    assert "needs_false_alarm_control" in report["blocking_gaps"]
    assert "needs_field_outcome_validation" in report["blocking_gaps"]
    assert "精准预测系统" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r6_research_product_value_support_rejects_unknown_metric_status():
    metrics = {
        "schema_version": "r6-trend-interval-risk-metrics-v1",
        "artifact_id": "bad-metrics",
        "status": "unsupported_status",
        "summary": {},
        "source_refs": ["source"],
        "blocking_gaps": [],
    }

    with pytest.raises(ValueError, match="trend_interval_risk_metrics.status"):
        build_r6_research_product_value_support(
            artifact_id="r6-research-product-value-support-bad",
            run_id="r6-product-value-run",
            trend_interval_risk_metrics=metrics,
        )


def test_r6_research_product_value_support_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-research-product-value-support.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_research_product_value_support.py",
            "--artifact-id",
            "r6-research-product-value-support-cli",
            "--run-id",
            "r6-product-value-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-research-product-value-support-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-research-product-value-support-cli",
        "output": str(output),
        "status": "product_value_support_partial",
        "overall_product_core_value_supported": False,
    }
