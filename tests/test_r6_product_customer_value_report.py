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
from experiments.r9_combination_comparison import build_r9_combination_comparison
from experiments.r9_false_alarm_gate_redesign import (
    build_r9_false_alarm_gate_redesign,
)
from experiments.r9_holdout_guard import build_r9_holdout_guard
from experiments.r9_synthetic_mechanism_lab import build_r9_synthetic_mechanism_lab


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


def test_r6_product_customer_value_report_cli_can_ingest_r9_paths(tmp_path):
    output = tmp_path / "r6-product-customer-value-report-r9.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_customer_value_report.py",
            "--artifact-id",
            "r6-product-customer-value-report-r9-cli",
            "--run-id",
            "r9-product-ingestion-run",
            "--output",
            str(output),
            "--r9-combination-comparison-path",
            "experiments/results/r9_combination_comparison/r9-combination-comparison-current-001.json",
            "--r9-synthetic-mechanism-lab-path",
            "experiments/results/r9_synthetic_mechanism_lab/r9-synthetic-mechanism-lab-current-001.json",
            "--r9-false-alarm-gate-redesign-path",
            "experiments/results/r9_false_alarm_gate_redesign/r9-false-alarm-gate-redesign-current-001.json",
            "--r9-holdout-guard-path",
            "experiments/results/r9_holdout_guard/r9-holdout-guard-current-001.json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert "r9_method_support" in artifact["display_payload"]
    assert artifact["display_payload"]["r9_method_support"][
        "holdout_guard_status"
    ] == "r9_holdout_guard_passed_guarded"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-product-customer-value-report-r9-cli",
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


def test_product_customer_value_report_can_show_r9_guarded_diagnostic_support():
    comparison = build_r9_combination_comparison(
        artifact_id="r9-combination-comparison-test",
        run_id="r9-product-ingestion-run",
    )
    synthetic_lab = build_r9_synthetic_mechanism_lab(
        artifact_id="r9-synthetic-mechanism-lab-test",
        run_id="r9-product-ingestion-run",
    )
    false_alarm_gate = build_r9_false_alarm_gate_redesign(
        artifact_id="r9-false-alarm-gate-redesign-test",
        run_id="r9-product-ingestion-run",
    )
    holdout_guard = build_r9_holdout_guard(
        artifact_id="r9-holdout-guard-test",
        run_id="r9-product-ingestion-run",
        combination_comparison=comparison,
        synthetic_mechanism_lab=synthetic_lab,
        false_alarm_gate_redesign=false_alarm_gate,
    )

    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r9-test",
        run_id="r9-product-ingestion-run",
        r9_combination_comparison=comparison,
        r9_synthetic_mechanism_lab=synthetic_lab,
        r9_false_alarm_gate_redesign=false_alarm_gate,
        r9_holdout_guard=holdout_guard,
    )

    assert "r9_method_support" in report["customer_sections"]
    r9_support = report["display_payload"]["r9_method_support"]
    assert r9_support["support_status"] == "guarded_diagnostic_candidate"
    assert r9_support["best_combination_id"] == "A+B+C"
    assert r9_support["metrics_beating_r7_v2"] == [
        "risk_ranking_quality",
        "decision_value_score",
    ]
    assert r9_support["holdout_guard_status"] == "r9_holdout_guard_passed_guarded"
    assert r9_support["false_alarm_gate_status"] == (
        "r9_false_alarm_gate_redesign_ready_guarded"
    )
    assert r9_support["synthetic_mechanism_recovery_passed"] is True
    assert r9_support["field_outcome_validated"] is False
    assert r9_support["runtime_default_allowed"] is False
    assert r9_support["blocked_claims"]
    for artifact in [comparison, synthetic_lab, false_alarm_gate, holdout_guard]:
        assert artifact["artifact_id"] in r9_support["source_artifact_ids"]
        assert artifact["artifact_id"] in report["source_refs"]
    section = next(
        item
        for item in report["section_contracts"]
        if item["section_id"] == "r9_method_support"
    )
    assert section["claim_status"] == "guarded_diagnostic"
    assert holdout_guard["artifact_id"] in section["source_artifact_ids"]
    assert "R9 validated" in report["blocked_claims"]
    assert "runtime default ready" in report["blocked_claims"]
