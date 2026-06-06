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
        "global_update_accepted": False,
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
        "l4_in_condition_transfer_passed": False,
        "global_update_accepted": False,
    }
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
    assert "outcome_feedback_fails_strong_prior_gate" in report["risk_flags"]
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
        "readiness_level": "L3_diagnostic_framework_not_L4_main_contribution",
        "decision": "not_ready_for_ccf_a_submission_as_main_algorithm",
        "short_answer": (
            "R6 has method framing, artifact governance, failure-boundary diagnosis, "
            "and Product evidence-chain value, but it has not passed L4 in-condition "
            "transfer or field validation, so it is not yet a CCF-A-level main "
            "contribution."
        ),
    }
    by_gate = {item["gate_id"]: item for item in report["readiness_checklist"]}
    assert by_gate["l4_in_condition_transfer"]["status"] == "failed"
    assert by_gate["strong_baseline_comparison"]["status"] == "failed"
    assert by_gate["field_or_real_outcome_validation"]["status"] == "failed"
    assert by_gate["product_claim_boundary"]["status"] == "passed"
    assert report["failed_required_gate_count"] == 6
    assert "needs_in_condition_same_family_rights_rule_holdout" in report["blocking_gaps"]
    assert "needs_field_outcome_validation" in report["blocking_gaps"]
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
