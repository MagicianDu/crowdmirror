import json
import subprocess
import sys

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_case_matrix import build_r6_case_matrix
from experiments.r6_evidence_report import build_r6_evidence_report
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


def test_r6_public_outcome_proxy_binds_htops_public_ingestion_to_one_case():
    proxy = build_r6_public_outcome_proxy(
        artifact_id="r6-public-outcome-proxy-test",
        run_id="r6-public-outcome-proxy-run",
    )

    assert proxy["schema_version"] == "r6-public-outcome-proxy-v1"
    assert proxy["status"] == "public_proxy_ready"
    assert proxy["target_case_id"] == "generic-public-service-policy-change"
    assert proxy["public_source"]["source_artifact_id"] == (
        "policy-reaction-htops-2506-public-ingestion-001"
    )
    assert proxy["public_source"]["usable_row_count"] == 7317
    assert proxy["public_source"]["source_url"].startswith("https://www.census.gov/")
    assert proxy["metrics"]["observed_reject_proxy"] == 0.47
    assert proxy["outcome_override"]["metrics"]["observed_reject_proxy"] == 0.47
    assert "low_income_food_insecure" in proxy["outcome_override"]["by_segment"]
    assert "public_proxy_not_field_outcome" in proxy["data_quality_flags"]
    assert "not_field_validation" in proxy["risk_flags"]
    json.dumps(proxy, allow_nan=False)


def test_r6_public_outcome_proxy_binds_anes_health_heldout_to_second_case():
    proxy = build_r6_public_outcome_proxy(
        artifact_id="r6-public-outcome-proxy-anes-test",
        run_id="r6-public-outcome-proxy-anes-run",
        source_key="anes_health_heldout",
    )

    assert proxy["schema_version"] == "r6-public-outcome-proxy-v1"
    assert proxy["status"] == "public_proxy_ready"
    assert proxy["target_case_id"] == "generic-rights-rule-change"
    assert proxy["public_source"]["source_artifact_id"] == (
        "policy-reaction-anes-health-001-heldout"
    )
    assert proxy["public_source"]["source_name"] == "ANES 2024 public-use health heldout"
    assert proxy["public_source"]["usable_row_count"] == 954
    assert proxy["public_source"]["split_role"] == "heldout"
    assert proxy["metrics"]["observed_reject_proxy"] == 0.33
    assert proxy["mapping_review"]["target_response_option"] == "private_insurance_plan"
    assert "public_heldout_proxy_not_field_outcome" in proxy["data_quality_flags"]
    assert "heldout_public_proxy_not_global_validation" in proxy["risk_flags"]


def test_r6_case_matrix_can_replace_one_fixture_with_public_proxy_outcome():
    proxy = build_r6_public_outcome_proxy(
        artifact_id="r6-public-outcome-proxy-test",
        run_id="r6-public-outcome-proxy-run",
    )
    matrix = build_r6_case_matrix(
        artifact_id="r6-case-matrix-public-proxy-test",
        run_id="r6-case-matrix-public-proxy-run",
        public_outcome_proxy=proxy,
    )

    public_cases = [case for case in matrix["cases"] if case["outcome_source_level"] == "public_proxy"]
    assert matrix["case_count"] == 3
    assert matrix["public_outcome_proxy_case_count"] == 1
    assert public_cases[0]["case_id"] == "generic-public-service-policy-change"
    assert public_cases[0]["learning"]["observed_reject_proxy"] == 0.47
    assert "public_proxy_not_field_outcome" in public_cases[0]["data_quality_flags"]
    assert "case_templates_are_fixture_level_evidence" in matrix["risk_flags"]
    assert "one_case_has_public_outcome_proxy" in matrix["risk_flags"]


def test_r6_case_matrix_accepts_two_public_proxies_without_merging_sources():
    htops_proxy = build_r6_public_outcome_proxy(
        artifact_id="r6-public-outcome-proxy-htops-test",
        run_id="r6-public-outcome-proxy-htops-run",
    )
    anes_proxy = build_r6_public_outcome_proxy(
        artifact_id="r6-public-outcome-proxy-anes-test",
        run_id="r6-public-outcome-proxy-anes-run",
        source_key="anes_health_heldout",
    )
    matrix = build_r6_case_matrix(
        artifact_id="r6-case-matrix-two-proxy-test",
        run_id="r6-case-matrix-two-proxy-run",
        public_outcome_proxies=[htops_proxy, anes_proxy],
    )

    public_cases = [case for case in matrix["cases"] if case["outcome_source_level"] == "public_proxy"]
    assert matrix["public_outcome_proxy_case_count"] == 2
    assert {case["case_id"] for case in public_cases} == {
        "generic-public-service-policy-change",
        "generic-rights-rule-change",
    }
    assert {
        case["public_outcome_proxy_artifact_id"] for case in public_cases
    } == {
        "r6-public-outcome-proxy-htops-test",
        "r6-public-outcome-proxy-anes-test",
    }
    assert "two_cases_have_public_outcome_proxy" in matrix["risk_flags"]


def test_r6_ablation_report_compares_prior_interaction_noise_and_feedback():
    proxy = build_r6_public_outcome_proxy(
        artifact_id="r6-public-outcome-proxy-test",
        run_id="r6-public-outcome-proxy-run",
    )
    report = build_r6_ablation_report(
        artifact_id="r6-ablation-report-test",
        run_id="r6-ablation-report-run",
        public_outcome_proxy=proxy,
        seeds=[11, 17],
        scales=[3, 6],
    )

    assert report["schema_version"] == "r6-ablation-report-v1"
    assert report["status"] == "diagnostic_ready"
    assert report["target_case_id"] == "generic-public-service-policy-change"
    assert report["public_proxy"]["usable_row_count"] == 7317
    assert report["seed_scale_grid"] == {"seeds": [11, 17], "scales": [3, 6], "run_count": 4}
    assert report["deterministic_replay"]["passed"] is True

    methods = {result["method"] for result in report["baseline_results"]}
    assert {
        "no_interaction_prior",
        "random_noise_baseline",
        "uncalibrated_interaction",
        "prior_anchored_interaction",
        "outcome_feedback_update",
    } <= methods

    by_method = {result["method"]: result for result in report["baseline_results"]}
    assert by_method["prior_anchored_interaction"]["mean_absolute_error"] < (
        by_method["no_interaction_prior"]["mean_absolute_error"]
    )
    assert by_method["outcome_feedback_update"]["global_update_status"] == "blocked_same_case_only"
    assert report["current_best_non_feedback_method"] == "prior_anchored_interaction"
    assert report["claim_status"] == "public_proxy_diagnostic_only"


def test_r6_evidence_report_answers_continue_or_stoploss_boundary():
    report = build_r6_evidence_report(
        artifact_id="r6-evidence-report-test",
        run_id="r6-evidence-report-run",
    )

    assert report["schema_version"] == "r6-evidence-report-v1"
    assert report["status"] == "public_proxy_evidence_ready"
    assert report["evidence_answer"]["current_decision"] == "continue_r6_with_constraints"
    assert report["evidence_answer"]["stoploss_triggered"] is False
    assert report["acceptance_gates"] == {
        "public_outcome_proxy_connected": True,
        "second_public_outcome_proxy_connected": True,
        "ablation_baselines_present": True,
        "deterministic_replay_passed": True,
        "product_report_ingests_mechanism_cap": True,
        "global_update_accepted": False,
    }
    assert report["product_report_summary"]["mechanism_cap_status"] == (
        "diagnostic_candidate_not_runtime_default"
    )
    assert report["ablation_summary"]["prior_anchored_beats_no_interaction"] is True
    assert report["multi_proxy_summary"] == {
        "public_proxy_count": 2,
        "public_proxy_source_count": 2,
        "prior_anchored_positive_count": 1,
        "prior_anchored_regression_count": 1,
        "conclusion": "mixed_public_proxy_evidence",
    }
    assert "needs_more_public_or_real_outcomes" in report["remaining_gaps"]
    assert "needs_product_demo_report_ingestion" not in report["remaining_gaps"]
    assert "needs_public_proxy_mapping_review" not in report["remaining_gaps"]
    assert "same_case_feedback_not_global_acceptance" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_evidence_report_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-evidence-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_evidence_report.py",
            "--artifact-id",
            "r6-evidence-report-cli",
            "--run-id",
            "r6-evidence-report-run",
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
    assert report["schema_version"] == "r6-evidence-report-v1"
    assert report["status"] == "public_proxy_evidence_ready"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-evidence-report-cli",
        "decision": "continue_r6_with_constraints",
        "output": str(output),
        "status": "public_proxy_evidence_ready",
    }
