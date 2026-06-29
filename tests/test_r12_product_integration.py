import json
from pathlib import Path

from experiments.r6_product_api_manifest import build_r6_product_api_manifest
from experiments.r6_product_customer_value_report import (
    build_r6_product_customer_value_report,
)


def test_r12_product_support_gate_flows_into_customer_report_as_secondary_evidence():
    gate = _load_current_r12_product_support_gate()
    report = build_r6_product_customer_value_report(
        artifact_id="r6-product-customer-value-report-r12-integration",
        run_id="r12-product-integration-test",
        r12_product_support_gate=gate,
    )

    assert "r12_transfer_evidence" in report["customer_sections"]
    payload = report["display_payload"]["r12_transfer_evidence"]
    workflow_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_validation_workflow_status_boundary"
    ]
    assert workflow_boundary["current_stage"] == "source_arrival_pending"
    assert workflow_boundary["next_action"] == (
        "collect_customer_field_slice_or_wait_for_target_outcome"
    )
    assert workflow_boundary["product_default_allowed"] is False
    trial_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_readiness_package_boundary"
    ]
    assert trial_boundary["trial_package_status"] == (
        "r12_customer_trial_readiness_package_ready_guarded_source_pending"
    )
    assert trial_boundary["template_output_path"].endswith(
        "r12-customer-field-slice-template-current-001.csv"
    )
    assert trial_boundary["product_default_allowed"] is False
    operational_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_operational_check_boundary"
    ]
    assert operational_boundary["operational_check_status"] == (
        "r12_customer_trial_operational_check_ready_source_pending"
    )
    assert operational_boundary["customer_trial_request_operationally_ready"] is True
    assert operational_boundary["source_registry_resolvable"] is True
    assert operational_boundary["field_outcome_validated"] is False
    assert operational_boundary["product_default_allowed"] is False
    launch_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_launch_handoff_package_boundary"
    ]
    assert launch_boundary["launch_package_status"] == (
        "r12_customer_trial_launch_handoff_package_ready_source_pending"
    )
    assert launch_boundary["launch_handoff_ready"] is True
    assert launch_boundary["minimum_case_count"] == 10
    assert launch_boundary["field_outcome_validated"] is False
    assert launch_boundary["product_default_allowed"] is False
    packet_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_launch_packet_export_boundary"
    ]
    assert packet_boundary["packet_export_status"] == (
        "r12_customer_trial_launch_packet_export_ready_source_pending"
    )
    assert packet_boundary["markdown_export_written"] is True
    assert packet_boundary["customer_field_slice_present"] is False
    assert packet_boundary["field_outcome_validated"] is False
    assert packet_boundary["product_default_allowed"] is False
    bundle_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_launch_bundle_verification_boundary"
    ]
    assert bundle_boundary["bundle_verification_status"] == (
        "r12_customer_trial_launch_bundle_verification_ready_source_pending"
    )
    assert bundle_boundary["launch_bundle_verified"] is True
    assert bundle_boundary["required_item_count"] == 4
    assert bundle_boundary["resolved_required_item_count"] == 4
    assert bundle_boundary["field_outcome_validated"] is False
    assert bundle_boundary["product_default_allowed"] is False
    operator_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_field_slice_operator_rehearsal_boundary"
    ]
    assert operator_boundary["operator_rehearsal_status"] == (
        "r12_customer_field_slice_operator_rehearsal_ready_no_field_claim"
    )
    assert operator_boundary["operator_command_rehearsed"] is True
    assert operator_boundary["sample_slice_ready_for_revalidation"] is True
    assert operator_boundary["real_customer_field_slice_submitted"] is False
    assert operator_boundary["field_outcome_validated"] is False
    assert operator_boundary["product_default_allowed"] is False
    feedback_loop_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_feedback_loop_operator_rehearsal_boundary"
    ]
    assert feedback_loop_boundary["feedback_loop_rehearsal_status"] == (
        "r12_customer_feedback_loop_operator_rehearsal_ready_no_field_claim"
    )
    assert feedback_loop_boundary["l22_intake_validator_executed"] is True
    assert feedback_loop_boundary["l23_field_revalidation_executed"] is True
    assert feedback_loop_boundary["l24_feedback_candidates_generated"] is True
    assert feedback_loop_boundary["l25_shadow_replay_executed"] is True
    assert feedback_loop_boundary["l26_synthetic_holdout_review_executed"] is True
    assert feedback_loop_boundary["real_customer_field_slice_submitted"] is False
    assert feedback_loop_boundary["field_outcome_validated"] is False
    assert feedback_loop_boundary["product_default_allowed"] is False
    ledger_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_evidence_ledger_boundary"
    ]
    assert ledger_boundary["ledger_status"] == (
        "r12_customer_trial_evidence_ledger_ready_source_pending"
    )
    assert ledger_boundary["launch_bundle_verified"] is True
    assert ledger_boundary["operator_rehearsal_executed"] is True
    assert ledger_boundary["feedback_loop_rehearsed_l22_to_l26"] is True
    assert ledger_boundary["blocking_gap_count"] == 3
    assert ledger_boundary["field_outcome_validated"] is False
    assert ledger_boundary["product_default_allowed"] is False
    assert payload == {
        "support_status": "guarded_transfer_positive_secondary_evidence",
        "gate_status": "r12_product_support_gate_ready_guarded",
        "claim_level": "product_secondary_evidence_only",
        "metrics": {
            "update_transfer_gain": 0.001287,
            "validation_mean_absolute_error_delta": -0.000431,
            "holdout_mean_absolute_error_delta": -0.000856,
            "interval_coverage_delta": 0.0,
            "false_alarm_rate_delta": 0.0,
        },
        "evidence_summary": gate["transfer_evidence_card"]["evidence_summary"],
        "primary_decision_source": "guarded_baseline_customer_value_report",
        "r12_output_role": "secondary_transfer_evidence_card_only",
        "r12_can_override_primary_decision": False,
        "public_data_validation_scope": gate["public_data_validation_scope"],
        "public_data_effectiveness_claim_allowed": gate["acceptance_gates"][
            "r12_public_data_effectiveness_claim_allowed"
        ],
        "customer_field_validation_required_for_current_stage": gate[
            "acceptance_gates"
        ]["customer_field_validation_required_for_current_stage"],
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "outcome_review_handoff": gate["outcome_review_handoff"],
        "blocked_claims": gate["blocked_claims"],
        "source_artifact_ids": [gate["artifact_id"]],
    }
    r12_contract = next(
        item
        for item in report["section_contracts"]
        if item["section_id"] == "r12_transfer_evidence"
    )
    assert r12_contract == {
        "section_id": "r12_transfer_evidence",
        "claim_status": "secondary_evidence_only",
        "source_artifact_ids": [gate["artifact_id"]],
        "blocked_claims": gate["blocked_claims"],
    }
    registry_ids = {entry["artifact_id"] for entry in report["source_registry"]}
    assert gate["artifact_id"] in registry_ids
    assert "r12-transfer-validation-current-001" in registry_ids
    assert "r12-customer-validation-workflow-status-current-001" in registry_ids
    assert "r12-customer-trial-readiness-package-current-001" in registry_ids
    assert "r12-customer-trial-operational-check-current-001" in registry_ids
    assert "r12-customer-trial-launch-handoff-package-current-001" in registry_ids
    assert "r12-customer-trial-launch-packet-export-current-001" in registry_ids
    assert "r12-customer-trial-launch-bundle-verification-current-001" in registry_ids
    assert "r12-customer-field-slice-operator-rehearsal-current-001" in registry_ids
    assert "r12-customer-feedback-loop-operator-rehearsal-current-001" in registry_ids
    assert "r12-customer-trial-evidence-ledger-current-001" in registry_ids
    assert gate["artifact_id"] in report["source_refs"]
    assert "R12 supports Product core method by default" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_product_support_gate_is_exposed_by_product_api_manifest():
    manifest = build_r6_product_api_manifest(
        artifact_id="r6-product-api-manifest-r12-integration",
        run_id="r12-product-integration-test",
    )

    assert manifest["artifact_refs"]["r12_product_support_gate"] == (
        "r12-product-support-gate-current-001"
    )
    endpoint = next(
        item
        for item in manifest["endpoints"]
        if item["endpoint_id"] == "r12_transfer_evidence"
    )
    assert endpoint == {
        "endpoint_id": "r12_transfer_evidence",
        "method": "GET",
        "path": "/r6/product/r12-transfer-evidence",
        "source_artifact_ids": ["r12-product-support-gate-current-001"],
        "response_contract": "source_artifact_json",
    }
    assert "r12_transfer_evidence" in manifest["display_contract"][
        "required_sections"
    ]
    assert "r12-product-support-gate-current-001" in manifest["source_refs"]
    registry_ids = {entry["artifact_id"] for entry in manifest["source_registry"]}
    assert "r12-customer-validation-workflow-status-current-001" in registry_ids
    assert "r12-customer-trial-readiness-package-current-001" in registry_ids
    assert "r12-customer-trial-operational-check-current-001" in registry_ids
    assert "r12-customer-trial-launch-handoff-package-current-001" in registry_ids
    assert "r12-customer-trial-launch-packet-export-current-001" in registry_ids
    assert "r12-customer-trial-launch-bundle-verification-current-001" in registry_ids
    assert "r12-customer-field-slice-operator-rehearsal-current-001" in registry_ids
    assert "r12-customer-feedback-loop-operator-rehearsal-current-001" in registry_ids
    assert "r12-customer-trial-evidence-ledger-current-001" in registry_ids
    assert "r12-customer-validation-workflow-status-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-trial-readiness-package-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-trial-operational-check-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-trial-launch-handoff-package-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-trial-launch-packet-export-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-trial-launch-bundle-verification-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-field-slice-operator-rehearsal-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-feedback-loop-operator-rehearsal-current-001" in manifest[
        "source_refs"
    ]
    assert "r12-customer-trial-evidence-ledger-current-001" in manifest[
        "source_refs"
    ]
    assert manifest["api_contract"]["runtime_default_allowed"] is False
    assert manifest["api_contract"]["field_outcome_validated"] is False
    json.dumps(manifest, allow_nan=False)


def _load_current_r12_product_support_gate():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_product_support_gate/"
            "r12-product-support-gate-current-001.json"
        ).read_text()
    )
