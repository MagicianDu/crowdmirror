import json
import subprocess
import sys

from experiments.r6_contracts import R6_CLAIM_BOUNDARY
from experiments.r6_case_matrix import build_r6_case_matrix
from experiments.r6_case_templates import R6_CASE_TEMPLATES, get_r6_case_template
from experiments.r6_product_report import build_r6_product_report


def test_r6_case_templates_cover_three_generic_change_types():
    assert len(R6_CASE_TEMPLATES) == 3
    assert {template["case_type"] for template in R6_CASE_TEMPLATES} == {
        "price_change",
        "rights_rule_change",
        "public_service_policy_change",
    }
    assert all(template["industry_binding"] == "generic" for template in R6_CASE_TEMPLATES)
    assert all(template["prior_segments"] for template in R6_CASE_TEMPLATES)
    assert all(template["scenario"]["impact_dimensions"] for template in R6_CASE_TEMPLATES)
    assert all(template["outcome"]["metrics"]["observed_reject_proxy"] > 0 for template in R6_CASE_TEMPLATES)

    template = get_r6_case_template("generic-rights-rule-change")
    assert template["case_type"] == "rights_rule_change"
    assert template["scenario"]["change_type"] == "rule"


def test_r6_case_matrix_runs_all_templates_through_outcome_feedback_chain():
    matrix = build_r6_case_matrix(
        artifact_id="r6-case-matrix-test",
        run_id="r6-case-matrix-run",
    )

    assert matrix["schema_version"] == "r6-case-matrix-v1"
    assert matrix["artifact_id"] == "r6-case-matrix-test"
    assert matrix["run_id"] == "r6-case-matrix-run"
    assert matrix["case_count"] == 3
    assert matrix["case_types_covered"] == [
        "price_change",
        "rights_rule_change",
        "public_service_policy_change",
    ]
    assert matrix["claim_boundaries"] == [R6_CLAIM_BOUNDARY]
    assert "no_cross_domain_accuracy_claim" in matrix["risk_flags"]
    assert matrix["acceptance_gates"] == {
        "minimum_case_templates_met": True,
        "all_cases_have_no_interaction_control": True,
        "all_cases_have_outcome_feedback": True,
        "all_updates_blocked_until_validated": True,
    }

    for case in matrix["cases"]:
        assert case["status"] == "diagnostic_ready"
        assert case["industry_binding"] == "generic"
        assert case["no_interaction_control_enabled"] is True
        assert case["risk_shift"]["delta"] > 0
        assert case["learning"]["absolute_error"] >= 0
        assert case["update_status"] == "needs_more_outcomes"
        assert case["top_risk_segment"]

    json.dumps(matrix, allow_nan=False)


def test_r6_product_report_exposes_pre_release_and_post_release_sections():
    matrix = build_r6_case_matrix(
        artifact_id="r6-case-matrix-test",
        run_id="r6-case-matrix-run",
    )
    report = build_r6_product_report(
        artifact_id="r6-product-report-test",
        run_id="r6-product-report-run",
        case_matrix=matrix,
    )

    assert report["schema_version"] == "r6-product-report-v1"
    assert report["status"] == "report_ready"
    assert report["decision_support"]["primary_use"] == (
        "pre_release_risk_review_and_post_release_learning"
    )
    assert report["decision_support"]["market_claim_status"] == (
        "diagnostic_workflow_ready_not_accuracy_claim"
    )
    assert report["claim_boundary"] == R6_CLAIM_BOUNDARY
    assert len(report["pre_release"]["case_summaries"]) == 3
    assert len(report["post_release_review"]["case_reviews"]) == 3
    assert "observed_reject_proxy_by_segment" in report["outcome_collection_checklist"]
    assert report["next_actions"] == [
        "collect_real_or_proxy_outcomes_for_each_release",
        "review_error_attribution_before_enabling_updates",
        "add_holdout_or_follow_up_cases_before_accepting_global_updates",
    ]

    first = report["pre_release"]["case_summaries"][0]
    assert {"static_prior", "interaction_shift", "top_risk_segment"} <= set(first)
    assert first["interaction_shift"]["claim_status"] == "risk_hypothesis"


def test_r6_product_report_cli_writes_report(tmp_path):
    output = tmp_path / "r6-product-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_report.py",
            "--artifact-id",
            "r6-product-report-cli",
            "--run-id",
            "r6-product-report-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-product-report-v1"
    assert report["source_case_matrix"]["case_count"] == 3
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-product-report-cli",
        "case_count": 3,
        "output": str(output),
        "status": "report_ready",
    }
