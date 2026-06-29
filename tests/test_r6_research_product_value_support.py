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


def test_r6_research_product_value_support_has_actionable_gap_ledger():
    report = build_r6_research_product_value_support(
        artifact_id="r6-research-product-value-support-test",
        run_id="r6-product-value-run",
    )

    assert report["acceptance_gates"] == {
        "all_product_values_mapped": True,
        "all_gaps_have_research_tasks": True,
        "all_tasks_have_acceptance_criteria": True,
        "research_next_tasks_executed": True,
        "research_support_contract_complete": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "overall_product_core_value_supported": False,
    }
    assert report["research_next_task_execution_summary"] == {
        "artifact_id": "r6-research-next-task-execution-current-001",
        "status": "research_next_tasks_executed_with_guarded_results",
        "task_count": 5,
        "accepted_for_guarded_reporting_count": 1,
        "blocked_or_failed_count": 4,
        "product_core_value_fully_supported": False,
    }
    assert "r6-research-next-task-execution-current-001" in report["source_refs"]
    assert report["support_coverage"] == {
        "product_value_count": 6,
        "supported_value_count": 0,
        "partial_value_count": 2,
        "diagnostic_value_count": 3,
        "blocked_value_count": 1,
        "research_support_contract_complete": True,
    }
    ledger = report["support_gap_ledger"]
    assert {item["product_value"] for item in ledger} == {
        "trend_direction",
        "risk_interval",
        "risk_distribution",
        "abnormal_segments",
        "mechanism_explanation",
        "outcome_feedback_learning",
    }
    for item in ledger:
        assert item["current_support_status"]
        assert item["product_display_level"] in {
            "guarded_partial_claim",
            "guarded_diagnostic_claim",
            "diagnostic_claim_only",
            "blocked_claim_only",
        }
        assert item["blocking_gap_ids"]
        assert item["next_research_task_id"]
        assert item["acceptance_criteria"]
        assert item["source_artifact_ids"]

    trend_gap = _ledger_item(ledger, "trend_direction")
    assert trend_gap["current_metric_value"] == 0.667
    assert trend_gap["target_threshold"] == 0.8
    assert trend_gap["gap_to_target"] == 0.133
    assert trend_gap["product_display_level"] == "guarded_partial_claim"

    risk_gap = _ledger_item(ledger, "risk_distribution")
    assert risk_gap["current_metric_value"] == {
        "risk_ranking_quality": 0.333,
        "false_alarm_rate": 0.667,
    }
    assert risk_gap["target_threshold"] == {
        "risk_ranking_quality_min": 0.5,
        "false_alarm_rate_max": 0.5,
    }
    assert risk_gap["gap_to_target"] == {
        "risk_ranking_gap": 0.167,
        "false_alarm_gap": 0.167,
    }

    summary = report["product_claim_support_summary"]
    assert summary["research_support_contract_complete"] is True
    assert summary["overall_product_core_value_supported"] is False
    assert summary["guarded_partial_claims_supported"] == [
        "trend_direction",
        "risk_interval",
    ]
    assert "outcome_feedback_learning" in summary["blocked_product_values"]

    task_ids = {task["task_id"] for task in report["research_next_tasks"]}
    assert task_ids == {item["next_research_task_id"] for item in ledger}
    for task in report["research_next_tasks"]:
        assert task["goal"]
        assert task["implementation_path"]
        assert task["acceptance_criteria"]
        assert task["unblocks_product_values"]


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


def _ledger_item(ledger, product_value):
    for item in ledger:
        if item["product_value"] == product_value:
            return item
    raise AssertionError(f"missing ledger item: {product_value}")
