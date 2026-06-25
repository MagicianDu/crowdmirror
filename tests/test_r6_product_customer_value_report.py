import json
import subprocess
import sys

from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)
from experiments.r8_robustness_holdout_gate import build_r8_robustness_holdout_gate
from experiments.r8_stop_loss_diagnosis import build_r8_stop_loss_diagnosis
from experiments.r8_product_failure_diagnosis_package import (
    build_r8_product_failure_diagnosis_package,
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
        "counterfactual_policy_comparison",
        "research_support_gap_ledger",
        "evidence_and_blocked_claims",
        "outcome_review_plan",
    ]
    assert "trend_direction" in report["display_payload"]
    assert "risk_interval" in report["display_payload"]
    assert "risk_distribution" in report["display_payload"]
    assert "abnormal_segments" in report["display_payload"]
    assert "counterfactual_policy_comparison" in report["display_payload"]
    assert "research_support" in report["display_payload"]
    assert report["display_payload"]["research_support"][
        "overall_product_core_value_supported"
    ] is False
    assert report["display_payload"]["research_support"]["support_gap_ledger"]
    assert "精准预测系统" in report["blocked_claims"]
    assert "r6-research-product-value-support-v2-current-001" in report["source_refs"]
    assert report["display_payload"]["risk_interval"]["support_status"] == (
        "guarded_interval_supported"
    )
    assert report["display_payload"]["counterfactual_policy_comparison"][
        "support_status"
    ] == "guarded_current_proxy_positive_signal"
    assert report["display_payload"]["research_support"]["support_coverage"][
        "supported_value_count"
    ] >= 1
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


def test_product_customer_value_report_can_ingest_r8_support_gate():
    r8_gate = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-product-ingestion-run",
    )
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r8-test",
        run_id="r8-product-ingestion-run",
        r8_robustness_holdout_gate=r8_gate,
    )

    assert "r8_method_support" in report["customer_sections"]
    assert "r8_method_support" in report["display_payload"]
    assert report["display_payload"]["r8_method_support"]["status"] == r8_gate["status"]
    assert report["display_payload"]["r8_method_support"][
        "runtime_default_allowed"
    ] is False
    assert report["display_payload"]["r8_method_support"][
        "field_outcome_validated"
    ] is False
    assert r8_gate["artifact_id"] in report["source_refs"]
    assert "R8 validated" in report["blocked_claims"]
    assert "runtime default ready" in report["blocked_claims"]


def test_product_customer_value_report_can_show_r8_stop_loss_diagnosis():
    r8_gate = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-product-ingestion-run",
    )
    diagnosis = build_r8_stop_loss_diagnosis(
        artifact_id="r8-stop-loss-diagnosis-test",
        run_id="r8-product-ingestion-run",
        robustness_holdout_gate=r8_gate,
    )
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r8-diagnosis-test",
        run_id="r8-product-ingestion-run",
        r8_robustness_holdout_gate=r8_gate,
        r8_stop_loss_diagnosis=diagnosis,
    )

    r8_support = report["display_payload"]["r8_method_support"]
    assert r8_support["diagnosis_status"] == "r8_stop_loss_diagnosis_ready"
    assert r8_support["root_causes"] == diagnosis["root_causes"]
    assert r8_support["recommended_next_tracks"] == diagnosis[
        "recommended_next_tracks"
    ]
    assert diagnosis["artifact_id"] in r8_support["source_artifact_ids"]
    assert diagnosis["artifact_id"] in report["source_refs"]
    section = next(
        item
        for item in report["section_contracts"]
        if item["section_id"] == "r8_method_support"
    )
    assert diagnosis["artifact_id"] in section["source_artifact_ids"]


def test_product_customer_value_report_can_show_r8_failure_diagnosis_package():
    r8_gate = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-product-ingestion-run",
    )
    diagnosis = build_r8_stop_loss_diagnosis(
        artifact_id="r8-stop-loss-diagnosis-test",
        run_id="r8-product-ingestion-run",
        robustness_holdout_gate=r8_gate,
    )
    failure_package = build_r8_product_failure_diagnosis_package(
        artifact_id="r8-product-failure-diagnosis-package-test",
        run_id="r8-product-ingestion-run",
        stop_loss_diagnosis=diagnosis,
    )
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r8-failure-package-test",
        run_id="r8-product-ingestion-run",
        r8_robustness_holdout_gate=r8_gate,
        r8_stop_loss_diagnosis=diagnosis,
        r8_product_failure_diagnosis_package=failure_package,
    )

    r8_support = report["display_payload"]["r8_method_support"]
    assert r8_support["failure_diagnosis_package_status"] == (
        "r8_product_failure_diagnosis_package_ready_guarded"
    )
    assert r8_support["failure_cards"] == failure_package["failure_cards"]
    assert r8_support["evidence_requests"] == failure_package["evidence_requests"]
    assert r8_support["outcome_replay_workflow"] == failure_package[
        "outcome_replay_workflow"
    ]
    assert failure_package["artifact_id"] in r8_support["source_artifact_ids"]
    assert failure_package["artifact_id"] in report["source_refs"]
    section = next(
        item
        for item in report["section_contracts"]
        if item["section_id"] == "r8_method_support"
    )
    assert failure_package["artifact_id"] in section["source_artifact_ids"]
