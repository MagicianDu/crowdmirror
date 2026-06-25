import json
import subprocess
import sys

from experiments.r6_product_claim_evidence_registry import (
    build_r6_product_claim_evidence_registry,
    build_r6_research_product_value_support_v2,
)
from experiments.r6_segment_risk_reports import (
    build_r6_abnormal_segment_validation_report,
    build_r6_segment_risk_ranking_report,
)


def test_wp3_segment_risk_ranking_supports_guarded_risk_distribution():
    report = build_r6_segment_risk_ranking_report(
        artifact_id="r6-segment-risk-ranking-report-test",
        run_id="r6-full-product-support-run",
    )

    assert report["schema_version"] == "r6-segment-risk-ranking-report-v1"
    assert report["status"] == "segment_risk_ranking_supported_guarded_proxy"
    assert report["claim_status"] == "guarded"
    assert report["summary"]["risk_ranking_quality"] == 1.0
    assert report["summary"]["top_k_segment_precision"] == 0.667
    assert report["summary"]["segment_recall"] == 1.0
    assert report["summary"]["static_prior_miss_recovery_rate"] == 1.0
    assert report["summary"]["interaction_only_risk_discovery_count"] == 1
    assert report["acceptance_gates"]["risk_ranking_quality_passed"] is True
    assert report["acceptance_gates"]["top_k_segment_precision_passed"] is True
    assert report["acceptance_gates"]["segment_recall_passed"] is True
    assert report["acceptance_gates"]["field_segment_labels_available"] is False

    segment_types = {
        segment["segment_type"]
        for case in report["case_results"]
        for segment in case["segments"]
    }
    assert {
        "interaction_amplified_risk",
        "static_prior_missed_risk",
        "false_alarm_candidate",
    } <= segment_types
    for case in report["case_results"]:
        for segment in case["segments"]:
            assert segment["source_artifact_ids"]
            assert segment["risk_reason"]
            assert segment["uncertainty_level"] in {"medium", "diagnostic_only"}
    json.dumps(report, allow_nan=False)


def test_wp3_abnormal_segment_validation_keeps_proxy_label_boundary():
    report = build_r6_abnormal_segment_validation_report(
        artifact_id="r6-abnormal-segment-validation-report-test",
        run_id="r6-full-product-support-run",
    )

    assert report["schema_version"] == "r6-abnormal-segment-validation-report-v1"
    assert report["status"] == "abnormal_segment_validation_guarded_proxy"
    assert report["label_source_type"] == "proxy_aligned_audit_fixture_not_field_outcome"
    assert report["summary"]["segment_precision"] == 0.667
    assert report["summary"]["segment_recall"] == 1.0
    assert report["acceptance_gates"]["segment_metrics_computable"] is True
    assert report["acceptance_gates"]["field_segment_labels_available"] is False
    assert report["claim_status"] == "guarded"
    assert "field_outcome_validated=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_wp7_product_claim_evidence_registry_maps_all_product_sections():
    registry = build_r6_product_claim_evidence_registry(
        artifact_id="r6-product-claim-evidence-registry-test",
        run_id="r6-full-product-support-run",
    )

    assert registry["schema_version"] == "r6-product-claim-evidence-registry-v1"
    assert registry["status"] == "product_claim_evidence_registry_ready_guarded"
    expected_sections = {
        "trend_direction",
        "risk_interval",
        "risk_distribution",
        "abnormal_segments",
        "mechanism_explanation",
        "false_alarm_control",
        "outcome_feedback",
        "bounded_update_candidate",
    }
    assert {claim["product_section"] for claim in registry["claim_results"]} == expected_sections
    assert registry["acceptance_gates"]["all_product_visible_claims_source_backed"] is True
    assert registry["acceptance_gates"]["no_source_claim_rejected"] is True
    assert registry["acceptance_gates"]["runtime_default_allowed"] is False
    assert registry["summary"]["supported_value_count"] >= 1
    assert registry["summary"]["validated_claim_count"] == 0
    statuses = {claim["claim_status"] for claim in registry["claim_results"]}
    assert statuses <= {"validated", "guarded", "diagnostic", "blocked"}
    json.dumps(registry, allow_nan=False)


def test_wp7_research_product_value_support_v2_upgrades_only_source_backed_values():
    report = build_r6_research_product_value_support_v2(
        artifact_id="r6-research-product-value-support-v2-test",
        run_id="r6-full-product-support-run",
    )

    assert report["schema_version"] == "r6-research-product-value-support-v2"
    assert report["status"] == "product_value_support_v2_partial_supported"
    assert report["overall_product_core_value_supported"] is False
    assert report["support_coverage"]["supported_value_count"] >= 1
    assert report["support_coverage"]["validated_value_count"] == 0
    assert report["acceptance_gates"]["supported_value_count_gt_zero"] is True
    assert report["acceptance_gates"]["all_product_values_mapped"] is True
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    support = {
        item["product_value"]: item["support_status"]
        for item in report["support_matrix"]
    }
    assert support["risk_distribution"] == "supported_current_proxy_guarded"
    assert support["risk_interval"] == "guarded_interval_supported"
    assert support["abnormal_segments"] == "guarded_proxy_supported"
    assert support["outcome_feedback"] == "blocked_until_feedback_protocol"
    assert "Research 已完整支撑 Product 全部核心价值" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_round2_cli_writes_segment_and_evidence_contract_artifacts(tmp_path):
    commands = [
        (
            "experiments/r6_segment_risk_reports.py",
            "r6-segment-risk-ranking-report-cli",
            "r6-segment-risk-ranking-report-v1",
            "segment_risk_ranking_supported_guarded_proxy",
        ),
        (
            "experiments/r6_product_claim_evidence_registry.py",
            "r6-product-claim-evidence-registry-cli",
            "r6-product-claim-evidence-registry-v1",
            "product_claim_evidence_registry_ready_guarded",
        ),
    ]

    for script, artifact_id, schema_version, status in commands:
        output = tmp_path / f"{artifact_id}.json"
        completed = subprocess.run(
            [
                sys.executable,
                script,
                "--artifact-id",
                artifact_id,
                "--run-id",
                "r6-full-product-support-run",
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 0, completed.stderr
        payload = json.loads(output.read_text())
        assert payload["schema_version"] == schema_version
        assert payload["status"] == status
        stdout = json.loads(completed.stdout)
        assert stdout["artifact_id"] == artifact_id
        assert stdout["status"] == status
