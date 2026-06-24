import json
import subprocess
import sys

from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)


def test_r6_product_customer_value_report_contains_trend_interval_risk_sections():
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-test",
        run_id="r6-customer-value-run",
    )

    assert report["schema_version"] == "r6-product-customer-value-report-v1"
    assert report["status"] == "customer_value_report_ready_guarded"
    assert report["positioning"] == "人群反应趋势与风险区间模拟器"
    assert report["report_contract"]["precise_point_prediction_allowed"] is False
    assert report["report_contract"]["customer_facing_ui_demo_ready"] is True
    assert report["customer_sections"] == [
        "static_prior_baseline",
        "trend_direction",
        "risk_interval",
        "risk_distribution",
        "abnormal_segments",
        "mechanism_explanation",
        "research_support_gap_ledger",
        "evidence_and_blocked_claims",
        "outcome_review_plan",
    ]
    assert "trend_direction" in report["display_payload"]
    assert "risk_interval" in report["display_payload"]
    assert "risk_distribution" in report["display_payload"]
    assert "abnormal_segments" in report["display_payload"]
    assert "research_support" in report["display_payload"]
    assert report["display_payload"]["research_support"][
        "overall_product_core_value_supported"
    ] is False
    assert report["display_payload"]["research_support"]["support_gap_ledger"]
    assert "精准预测系统" in report["blocked_claims"]
    assert "r6-research-product-value-support-current-001" in report["source_refs"]
    assert "needs_customer_facing_ui_integration" not in report["blocking_gaps"]
    assert "needs_customer_workflow_runtime_integration" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_product_customer_value_report_sources_are_resolvable():
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-test",
        run_id="r6-customer-value-run",
    )

    registry_ids = {entry["artifact_id"] for entry in report["source_registry"]}
    for source_ref in report["source_refs"]:
        assert source_ref in registry_ids or source_ref == report["artifact_id"]
    for section in report["section_contracts"]:
        assert section["source_artifact_ids"]
        for source_artifact_id in section["source_artifact_ids"]:
            assert source_artifact_id in registry_ids


def test_r6_product_customer_value_report_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-product-customer-value-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_customer_value_report.py",
            "--artifact-id",
            "r6-product-customer-value-report-cli",
            "--run-id",
            "r6-customer-value-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-product-customer-value-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-product-customer-value-report-cli",
        "output": str(output),
        "status": "customer_value_report_ready_guarded",
    }
