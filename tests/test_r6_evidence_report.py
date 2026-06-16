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


def test_r6_public_outcome_proxy_binds_anes_climate_heldout_to_third_same_family_case():
    proxy = build_r6_public_outcome_proxy(
        artifact_id="r6-public-outcome-proxy-anes-climate-test",
        run_id="r6-public-outcome-proxy-anes-climate-run",
        source_key="anes_climate_heldout",
    )

    assert proxy["schema_version"] == "r6-public-outcome-proxy-v1"
    assert proxy["status"] == "public_proxy_ready"
    assert proxy["source_key"] == "anes_climate_heldout"
    assert proxy["target_case_id"] == "generic-rights-rule-change"
    assert proxy["target_case_type"] == "rights_rule_change"
    assert proxy["public_source"]["source_artifact_id"] == (
        "policy-reaction-anes-climate-001-heldout"
    )
    assert proxy["public_source"]["source_name"] == (
        "ANES 2024 public-use climate-energy regulation heldout"
    )
    assert proxy["public_source"]["usable_row_count"] == 932
    assert proxy["public_source"]["split_role"] == "heldout"
    assert proxy["metrics"]["observed_reject_proxy"] == 0.25
    assert proxy["mapping_review"]["proxy_family"] == (
        "climate_energy_regulation_preference"
    )
    assert proxy["mapping_review"]["target_response_option"] == (
        "oppose_more_regulation_or_spending"
    )
    assert "same_dataset_regulation_holdout_proxy_not_field_outcome" in proxy[
        "data_quality_flags"
    ]
    assert "same_family_holdout_not_cap_condition_validation" in proxy["risk_flags"]


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
        "third_public_outcome_proxy_connected": True,
        "ablation_baselines_present": True,
        "deterministic_replay_passed": True,
        "product_report_ingests_mechanism_cap": True,
        "followup_holdout_validation_present": True,
        "mechanism_cap_same_family_holdout_available": True,
        "mechanism_cap_same_family_cap_condition_covered": False,
        "mechanism_cap_same_family_validation_passed": False,
        "outcome_feedback_cross_case_transfer_available": False,
        "cross_case_transfer_protocol_present": True,
        "outcome_feedback_transfer_beats_static_prior": False,
        "runtime_update_guard_passed": False,
        "decision_value_metrics_present": True,
        "decision_value_passed": False,
        "risk_discovery_holdout_validation_present": True,
        "risk_discovery_holdout_passed": False,
        "risk_discovery_threshold_sweep_present": True,
        "threshold_tuning_sufficient": False,
        "false_alarm_reducible_by_threshold": False,
        "false_alarm_discriminator_present": True,
        "false_alarm_discriminator_ready": False,
        "generalizable_false_alarm_discriminator_found": False,
        "interaction_signal_validity_present": True,
        "interaction_signal_validity_generalized": False,
        "current_proxy_supported_interaction_signal_observed": True,
        "interaction_signal_validity_holdout_validation_present": True,
        "interaction_signal_validity_holdout_passed": False,
        "risk_discovery_value_report_present": True,
        "static_prior_role_reframed_as_foundation": True,
        "risk_discovery_path_should_continue": True,
        "in_condition_holdout_ledger_present": True,
        "in_condition_holdout_found": False,
        "product_evidence_cards_present": True,
        "ccfa_readiness_report_present": True,
        "ccf_a_main_contribution_ready": False,
        "global_update_accepted": False,
    }
    assert report["followup_holdout_validation_summary"] == {
        "artifact_id": "r6-evidence-report-test-followup-holdout-validation",
        "status": "holdout_validation_partial",
        "mechanism_cap_upgrade_status": (
            "partial_pass_needs_in_condition_same_family_holdout"
        ),
        "outcome_feedback_upgrade_status": "blocked_same_case_only",
        "global_update_accepted": False,
    }
    assert report["product_report_summary"]["mechanism_cap_status"] == (
        "diagnostic_candidate_not_runtime_default"
    )
    assert report["cross_case_transfer_protocol_summary"] == {
        "artifact_id": "r6-evidence-report-test-cross-case-transfer-protocol",
        "status": "transfer_protocol_ready_global_update_blocked",
        "mechanism_cap_l4_in_condition_transfer_passed": False,
        "outcome_feedback_transfer_beats_prior_interaction": True,
        "outcome_feedback_transfer_beats_static_prior": False,
        "runtime_update_guard_passed": False,
        "risk_discovery_value_path_open": True,
        "global_update_accepted": False,
    }
    assert report["risk_discovery_value_summary"] == {
        "artifact_id": "r6-evidence-report-test-risk-discovery-value-report",
        "status": "risk_discovery_value_partial_decision_metric_failed_holdout",
        "static_prior_role": "foundation_not_opponent",
        "r6_overall_worth_continuing": True,
        "runtime_update_default_ready": False,
        "decision_value_passed": False,
        "risk_discovery_holdout_passed": False,
        "false_alarm_discriminator_ready": False,
        "interaction_signal_validity_generalized": False,
        "interaction_signal_validity_holdout_passed": False,
    }
    assert report["decision_value_metrics_summary"] == {
        "artifact_id": "r6-evidence-report-test-decision-value-metrics",
        "status": "decision_value_partial_high_false_alarm",
        "decision_value_passed": False,
        "static_prior_miss_recovery_rate": 1.0,
        "top_k_risk_hit_rate": 0.333,
        "false_alarm_rate": 0.667,
    }
    assert report["risk_discovery_threshold_sweep_summary"] == {
        "artifact_id": "r6-evidence-report-test-risk-discovery-threshold-sweep",
        "status": "threshold_sweep_no_separating_rule",
        "passing_threshold_found": False,
        "separating_threshold_found": False,
        "false_alarm_reducible_by_threshold": False,
        "best_threshold": 0.0,
        "true_signal_false_alarm_delta_overlap": True,
    }
    assert report["false_alarm_discriminator_summary"] == {
        "artifact_id": "r6-evidence-report-test-false-alarm-discriminator",
        "status": "false_alarm_discriminator_diagnostic_only",
        "current_proxy_separation_found": True,
        "pre_outcome_safe_candidate_found": True,
        "generalizable_discriminator_found": False,
        "accepted_candidate_count": 0,
        "false_alarm_discriminator_ready": False,
    }
    assert report["interaction_signal_validity_summary"] == {
        "artifact_id": "r6-evidence-report-test-interaction-signal-validity",
        "status": "interaction_signal_validity_diagnostic_only",
        "mean_validity_score": 0.763,
        "current_proxy_supported_signal_count": 1,
        "rejected_false_alarm_count": 2,
        "accepted_count": 0,
        "interaction_signal_validity_generalized": False,
    }
    assert report["interaction_signal_validity_holdout_summary"] == {
        "artifact_id": "r6-evidence-report-test-interaction-signal-validity-holdout-validation",
        "status": "interaction_signal_validity_holdout_failed_current_public_proxies",
        "source_supported_count": 1,
        "eligible_independent_holdout_count": 2,
        "passed_holdout_count": 0,
        "contradicted_holdout_count": 2,
        "interaction_signal_validity_holdout_passed": False,
    }
    assert report["risk_discovery_holdout_validation_summary"] == {
        "artifact_id": "r6-evidence-report-test-risk-discovery-holdout-validation",
        "status": "risk_discovery_holdout_failed_current_public_proxies",
        "risk_discovery_holdout_passed": False,
        "same_family_trial_count": 2,
        "passed_trial_count": 0,
    }
    assert report["in_condition_holdout_ledger_summary"] == {
        "artifact_id": "r6-evidence-report-test-in-condition-holdout-ledger",
        "status": "ledger_ready_no_in_condition_holdout_found",
        "in_condition_holdout_count": 0,
        "global_update_data_gate_passed": False,
    }
    assert report["product_evidence_cards_summary"] == {
        "artifact_id": "r6-evidence-report-test-product-evidence-cards",
        "status": "product_evidence_cards_ready",
        "card_count": 5,
        "static_narrative_fallback_allowed": False,
    }
    assert report["ccfa_readiness_summary"] == {
        "artifact_id": "r6-evidence-report-test-ccfa-readiness-report",
        "status": "ccf_a_readiness_evaluated",
        "ccf_a_main_contribution_ready": False,
        "readiness_level": "L3_risk_discovery_framework_needs_validation",
        "failed_required_gate_count": 6,
    }
    assert report["ablation_summary"]["prior_anchored_beats_no_interaction"] is True
    assert report["multi_proxy_summary"] == {
        "public_proxy_count": 3,
        "public_proxy_source_count": 2,
        "prior_anchored_positive_count": 1,
        "prior_anchored_regression_count": 2,
        "conclusion": "mixed_public_proxy_evidence",
    }
    assert "needs_more_public_or_real_outcomes" in report["remaining_gaps"]
    assert "needs_product_demo_report_ingestion" not in report["remaining_gaps"]
    assert "needs_public_proxy_mapping_review" not in report["remaining_gaps"]
    assert "needs_third_public_or_real_proxy" not in report["remaining_gaps"]
    assert "needs_in_condition_same_family_rights_rule_holdout" in report[
        "remaining_gaps"
    ]
    assert "needs_runtime_update_guard_before_default_enablement" in report[
        "remaining_gaps"
    ]
    assert "needs_outcome_feedback_transfer_beating_static_prior" not in report[
        "remaining_gaps"
    ]
    assert "needs_risk_discovery_holdout_validation" in report["remaining_gaps"]
    assert "needs_decision_value_metric_to_pass" in report["remaining_gaps"]
    assert "needs_lower_false_alarm_rate" in report["remaining_gaps"]
    assert "needs_non_threshold_false_alarm_discriminator" not in report[
        "remaining_gaps"
    ]
    assert "needs_generalizable_false_alarm_discriminator" not in report[
        "remaining_gaps"
    ]
    assert "needs_discriminator_holdout_validation" not in report["remaining_gaps"]
    assert "needs_in_family_positive_signal" not in report["remaining_gaps"]
    assert "needs_interaction_signal_validity_generalization" in report[
        "remaining_gaps"
    ]
    assert "needs_signal_validity_holdout_validation" in report["remaining_gaps"]
    assert "needs_independent_supported_signal_holdout" in report["remaining_gaps"]
    assert "needs_positive_same_family_source_signal" in report["remaining_gaps"]
    assert "needs_field_outcome_validation" in report["remaining_gaps"]
    assert "same_case_feedback_not_global_acceptance" in report["risk_flags"]
    assert "static_prior_is_foundation_not_opponent" in report["risk_flags"]
    assert "false_alarm_discriminator_not_runtime_ready" in report["risk_flags"]
    assert "interaction_signal_validity_not_generalized" in report["risk_flags"]
    assert "ccf_a_main_contribution_not_ready" in report["risk_flags"]
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
