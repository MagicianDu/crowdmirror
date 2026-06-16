import json
import subprocess
import sys

from experiments.r6_ccfa_readiness_report import build_r6_ccfa_readiness_report
from experiments.r6_cross_case_transfer_protocol import (
    build_r6_cross_case_transfer_protocol,
)
from experiments.r6_in_condition_holdout_ledger import (
    build_r6_in_condition_holdout_ledger,
)
from experiments.r6_product_evidence_cards import build_r6_product_evidence_cards
from experiments.r6_risk_discovery_value_report import (
    build_r6_risk_discovery_value_report,
)


def test_r6_cross_case_transfer_protocol_blocks_global_update_at_l3_partial():
    report = build_r6_cross_case_transfer_protocol(
        artifact_id="r6-cross-case-transfer-test",
        run_id="r6-cross-case-transfer-run",
    )

    assert report["schema_version"] == "r6-cross-case-transfer-protocol-v1"
    assert report["status"] == "transfer_protocol_ready_global_update_blocked"
    assert report["acceptance_gates"] == {
        "cross_case_transfer_protocol_present": True,
        "mechanism_cap_source_fix_passed": True,
        "mechanism_cap_l4_in_condition_transfer_passed": False,
        "outcome_feedback_transfer_available": True,
        "outcome_feedback_transfer_beats_prior_interaction": True,
        "outcome_feedback_transfer_beats_static_prior": False,
        "runtime_update_guard_passed": False,
        "risk_discovery_value_path_open": True,
        "global_update_accepted": False,
    }
    assert report["static_prior_role"] == {
        "role": "foundation_not_opponent",
        "runtime_update_guard": "candidate_updates_must_not_hurt_static_prior_before_default_enablement",
        "research_value_gate": "interaction_layer_must_discover_auditable_risk_not_visible_in_static_prior",
    }

    by_type = {
        candidate["candidate_type"]: candidate
        for candidate in report["candidate_transfers"]
    }
    mechanism_cap = by_type["mechanism_cap"]
    assert mechanism_cap["evidence_level"] == "L3_partial"
    assert mechanism_cap["acceptance_gates"] == {
        "source_fix_passed": True,
        "cross_proxy_non_regression_passed": True,
        "same_family_holdout_available": True,
        "same_family_cap_condition_covered": False,
        "l4_in_condition_transfer_passed": False,
        "global_update_accepted": False,
    }
    assert [
        (trial["trial_id"], trial["transfer_status"])
        for trial in mechanism_cap["holdout_trials"]
    ] == [
        ("mechanism-cap:anes_health_heldout->htops_cost_pressure", "non_regression_only"),
        (
            "mechanism-cap:anes_health_heldout->anes_climate_heldout",
            "condition_not_covered",
        ),
    ]

    feedback = by_type["outcome_feedback_residual_transfer"]
    assert feedback["acceptance_gates"] == {
        "cross_case_transfer_available": True,
        "beats_prior_interaction_on_holdout": True,
        "beats_static_prior_on_holdout": False,
        "runtime_update_guard_passed": False,
        "l4_in_condition_transfer_passed": False,
        "global_update_accepted": False,
    }
    assert feedback["transfer_decision"]["decision"] == (
        "runtime_update_blocked_but_risk_discovery_continues"
    )
    assert [
        (
            trial["trial_id"],
            trial["transfer_status"],
            trial["static_prior_error"],
            trial["prior_anchored_error"],
            trial["updated_error"],
            trial["strong_prior_gate_passed"],
        )
        for trial in feedback["holdout_trials"]
    ] == [
        (
            "outcome-feedback:anes_health_heldout->anes_climate_heldout",
            "non_regression_only",
            0.06,
            0.13,
            0.1,
            False,
        ),
        (
            "outcome-feedback:anes_climate_heldout->anes_health_heldout",
            "non_regression_only",
            0.02,
            0.05,
            0.03,
            False,
        ),
    ]
    assert report["global_update_decision"]["accepted"] is False
    assert "mechanism_cap_l4_transfer_missing" in report["risk_flags"]
    assert "outcome_feedback_runtime_update_guard_failed" in report["risk_flags"]
    assert "needs_runtime_update_guard_before_default_enablement" in report[
        "blocking_gaps"
    ]
    assert "needs_outcome_feedback_transfer_beating_static_prior" not in report[
        "blocking_gaps"
    ]
    json.dumps(report, allow_nan=False)


def test_r6_risk_discovery_value_report_keeps_static_prior_as_foundation():
    report = build_r6_risk_discovery_value_report(
        artifact_id="r6-risk-discovery-value-test",
        run_id="r6-risk-discovery-value-run",
    )

    assert report["schema_version"] == "r6-risk-discovery-value-report-v1"
    assert report["status"] == "risk_discovery_value_partial_decision_metric_failed_holdout"
    assert report["objective_reframe"] == {
        "static_prior_role": "foundation_not_opponent",
        "interaction_role": "discover_auditable_risk_shifts_beyond_static_prior",
        "outcome_feedback_role": "learn_from_real_outcomes_under_runtime_guards",
    }
    assert report["risk_discovery_gates"] == {
        "static_prior_foundation_present": True,
        "interaction_delta_observable": True,
        "failure_boundary_detected": True,
        "product_evidence_cards_present": True,
        "in_condition_holdout_bound": False,
        "decision_value_metric_present": True,
        "decision_value_metric_passed": False,
        "threshold_sweep_present": True,
        "threshold_tuning_sufficient": False,
        "false_alarm_reducible_by_threshold": False,
        "false_alarm_discriminator_present": True,
        "false_alarm_discriminator_ready": False,
        "generalizable_false_alarm_discriminator_found": False,
        "interaction_signal_validity_present": True,
        "interaction_signal_validity_generalized": False,
        "current_proxy_supported_interaction_signal_observed": True,
        "risk_discovery_holdout_validation_present": True,
        "risk_discovery_holdout_passed": False,
        "field_outcome_validated": False,
    }
    assert report["decision_value_summary"] == {
        "artifact_id": "r6-risk-discovery-value-test-decision-value-metrics",
        "status": "decision_value_partial_high_false_alarm",
        "decision_value_passed": False,
        "static_prior_miss_recovery_rate": 1.0,
        "top_k_risk_hit_rate": 0.333,
        "false_alarm_rate": 0.667,
        "decision_regret_reduction": 1,
    }
    assert report["threshold_sweep_summary"] == {
        "artifact_id": "r6-risk-discovery-value-test-threshold-sweep",
        "status": "threshold_sweep_no_separating_rule",
        "passing_threshold_found": False,
        "separating_threshold_found": False,
        "false_alarm_reducible_by_threshold": False,
        "best_threshold": 0.0,
        "true_signal_false_alarm_delta_overlap": True,
    }
    assert report["false_alarm_discriminator_summary"] == {
        "artifact_id": "r6-risk-discovery-value-test-false-alarm-discriminator",
        "status": "false_alarm_discriminator_diagnostic_only",
        "current_proxy_separation_found": True,
        "pre_outcome_safe_candidate_found": True,
        "generalizable_discriminator_found": False,
        "accepted_candidate_count": 0,
        "false_alarm_discriminator_ready": False,
    }
    assert report["interaction_signal_validity_summary"] == {
        "artifact_id": "r6-risk-discovery-value-test-interaction-signal-validity",
        "status": "interaction_signal_validity_diagnostic_only",
        "mean_validity_score": 0.763,
        "current_proxy_supported_signal_count": 1,
        "rejected_false_alarm_count": 2,
        "accepted_count": 0,
        "interaction_signal_validity_generalized": False,
    }
    assert report["holdout_validation_summary"] == {
        "artifact_id": "r6-risk-discovery-value-test-risk-discovery-holdout-validation",
        "status": "risk_discovery_holdout_failed_current_public_proxies",
        "risk_discovery_holdout_passed": False,
        "same_family_trial_count": 2,
        "passed_trial_count": 0,
    }
    assert report["runtime_update_guard"] == {
        "beat_static_prior_required_for_default_update": True,
        "static_prior_gate_role": "runtime_update_guard_not_research_objective",
        "outcome_feedback_runtime_default_accepted": False,
    }
    assert report["decision"]["r6_overall_worth_continuing"] is True
    assert report["decision"]["runtime_update_default_ready"] is False
    assert "needs_lower_false_alarm_rate" in report["blocking_gaps"]
    assert "needs_non_threshold_false_alarm_discriminator" not in report[
        "blocking_gaps"
    ]
    assert "needs_generalizable_false_alarm_discriminator" not in report[
        "blocking_gaps"
    ]
    assert "needs_discriminator_holdout_validation" not in report["blocking_gaps"]
    assert "needs_in_family_positive_signal" not in report["blocking_gaps"]
    assert "needs_interaction_signal_validity_generalization" in report[
        "blocking_gaps"
    ]
    assert "needs_signal_validity_holdout_validation" in report["blocking_gaps"]
    assert "needs_positive_same_family_source_signal" in report["blocking_gaps"]
    assert "needs_runtime_update_guard_before_default_enablement" in report[
        "blocking_gaps"
    ]
    json.dumps(report, allow_nan=False)


def test_r6_in_condition_holdout_ledger_separates_source_out_of_family_and_out_of_condition_data():
    ledger = build_r6_in_condition_holdout_ledger(
        artifact_id="r6-holdout-ledger-test",
        run_id="r6-holdout-ledger-run",
    )

    assert ledger["schema_version"] == "r6-in-condition-holdout-ledger-v1"
    assert ledger["status"] == "ledger_ready_no_in_condition_holdout_found"
    assert ledger["summary"] == {
        "candidate_count": 3,
        "in_condition_holdout_count": 0,
        "same_family_out_of_condition_count": 1,
        "source_case_not_holdout_count": 1,
        "out_of_family_holdout_count": 1,
        "global_update_data_gate_passed": False,
    }
    by_key = {entry["source_key"]: entry for entry in ledger["ledger_entries"]}
    assert by_key["anes_health_heldout"]["ledger_status"] == "source_case_not_holdout"
    assert by_key["anes_health_heldout"]["condition_checks"] == {
        "same_family_rights_rule_case": True,
        "independent_holdout_not_source_case": False,
        "static_prior_error_lte_threshold": True,
        "original_reject_delta_gt_cap": True,
        "public_or_field_outcome_mapping_auditable": True,
    }
    assert by_key["anes_climate_heldout"]["ledger_status"] == "out_of_condition_holdout"
    assert by_key["anes_climate_heldout"]["metrics"]["static_prior_error"] == 0.06
    assert by_key["anes_climate_heldout"]["condition_checks"][
        "static_prior_error_lte_threshold"
    ] is False
    assert by_key["htops_cost_pressure"]["ledger_status"] == "out_of_family_holdout"
    assert ledger["next_search_profile"]["required_static_prior_error_lte"] == 0.03
    assert "no_in_condition_holdout_found" in ledger["risk_flags"]
    json.dumps(ledger, allow_nan=False)


def test_r6_product_evidence_cards_require_claim_status_and_artifact_sources():
    cards = build_r6_product_evidence_cards(
        artifact_id="r6-product-evidence-cards-test",
        run_id="r6-product-evidence-cards-run",
    )

    assert cards["schema_version"] == "r6-product-evidence-cards-v1"
    assert cards["status"] == "product_evidence_cards_ready"
    assert cards["card_count"] == 5
    assert cards["demo_api_contract"]["consume_only_artifact_fields"] is True
    assert cards["demo_api_contract"]["static_narrative_fallback_allowed"] is False
    for card in cards["cards"]:
        assert card["claim_status"]
        assert card["allowed_claims"]
        assert card["blocked_claims"]
        assert card["source_artifact_ids"]
    by_id = {card["card_id"]: card for card in cards["cards"]}
    assert by_id["mechanism-cap-transfer"]["claim_status"] == (
        "diagnostic_l3_partial_not_runtime_default"
    )
    assert by_id["outcome-feedback-transfer"]["claim_status"] == (
        "non_regression_only_not_global_update"
    )
    assert by_id["holdout-data-gap"]["claim_status"] == "data_gate_blocked"
    assert "accuracy_claim_blocked" in cards["risk_flags"]
    json.dumps(cards, allow_nan=False)


def test_r6_ccfa_readiness_report_says_not_ready_for_ccf_a_main_contribution():
    report = build_r6_ccfa_readiness_report(
        artifact_id="r6-ccfa-readiness-test",
        run_id="r6-ccfa-readiness-run",
    )

    assert report["schema_version"] == "r6-ccfa-readiness-report-v1"
    assert report["status"] == "ccf_a_readiness_evaluated"
    assert report["verdict"] == {
        "ccf_a_main_contribution_ready": False,
        "readiness_level": "L3_risk_discovery_framework_needs_validation",
        "decision": "not_ready_for_ccf_a_submission_as_main_algorithm",
        "short_answer": (
            "R6 should be evaluated as a static-prior anchored risk-discovery "
            "framework. The static prior is the simulation base, while interaction "
            "adds auditable risk hypotheses. The framework is not CCF-A-ready until "
            "risk-discovery holdout validation, decision-value metrics, generalized "
            "interaction signal validity, and field outcome validation are present."
        ),
    }
    by_gate = {item["gate_id"]: item for item in report["readiness_checklist"]}
    assert by_gate["static_prior_foundation"]["status"] == "passed"
    assert by_gate["risk_discovery_objective_defined"]["status"] == "passed"
    assert by_gate["decision_value_metric"]["status"] == "partial"
    assert by_gate["risk_discovery_holdout_validation"]["status"] == "failed"
    assert by_gate["interaction_signal_validity_generalized"]["status"] == "failed"
    assert by_gate["runtime_update_guard"]["required_for_ccf_a"] is False
    assert by_gate["runtime_update_guard"]["status"] == "failed"
    assert by_gate["field_or_real_outcome_validation"]["status"] == "failed"
    assert by_gate["product_claim_boundary"]["status"] == "passed"
    assert report["failed_required_gate_count"] == 5
    assert "needs_risk_discovery_holdout_validation" in report["blocking_gaps"]
    assert "needs_decision_value_metric_to_pass" in report["blocking_gaps"]
    assert "needs_interaction_signal_validity_generalization" in report[
        "blocking_gaps"
    ]
    assert "needs_field_outcome_validation" in report["blocking_gaps"]
    assert "needs_stable_superiority_over_strong_static_prior" not in report[
        "blocking_gaps"
    ]
    assert "not_ccf_a_ready" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_new_method_gate_clis_write_artifacts(tmp_path):
    commands = [
        (
            "experiments/r6_cross_case_transfer_protocol.py",
            "r6-cross-case-transfer-cli",
            "r6-cross-case-transfer-protocol-v1",
        ),
        (
            "experiments/r6_in_condition_holdout_ledger.py",
            "r6-holdout-ledger-cli",
            "r6-in-condition-holdout-ledger-v1",
        ),
        (
            "experiments/r6_product_evidence_cards.py",
            "r6-product-evidence-cards-cli",
            "r6-product-evidence-cards-v1",
        ),
        (
            "experiments/r6_ccfa_readiness_report.py",
            "r6-ccfa-readiness-cli",
            "r6-ccfa-readiness-report-v1",
        ),
        (
            "experiments/r6_risk_discovery_value_report.py",
            "r6-risk-discovery-value-cli",
            "r6-risk-discovery-value-report-v1",
        ),
        (
            "experiments/r6_decision_value_metrics.py",
            "r6-decision-value-metrics-cli",
            "r6-decision-value-metrics-v1",
        ),
        (
            "experiments/r6_risk_discovery_holdout_validation.py",
            "r6-risk-discovery-holdout-validation-cli",
            "r6-risk-discovery-holdout-validation-v1",
        ),
        (
            "experiments/r6_risk_discovery_threshold_sweep.py",
            "r6-risk-discovery-threshold-sweep-cli",
            "r6-risk-discovery-threshold-sweep-v1",
        ),
        (
            "experiments/r6_false_alarm_discriminator.py",
            "r6-false-alarm-discriminator-cli",
            "r6-false-alarm-discriminator-v1",
        ),
        (
            "experiments/r6_interaction_signal_validity.py",
            "r6-interaction-signal-validity-cli",
            "r6-interaction-signal-validity-v1",
        ),
    ]
    for script, artifact_id, schema_version in commands:
        output = tmp_path / f"{artifact_id}.json"
        completed = subprocess.run(
            [
                sys.executable,
                script,
                "--artifact-id",
                artifact_id,
                "--run-id",
                "r6-method-gate-run",
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
        assert report["schema_version"] == schema_version
        assert json.loads(completed.stdout)["artifact_id"] == artifact_id
