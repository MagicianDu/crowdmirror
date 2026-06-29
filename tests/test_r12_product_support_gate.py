import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_product_support_gate import (
    R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION,
    build_r12_product_support_gate,
)
from experiments.r12_high_risk_holdout_registry import (
    build_r12_high_risk_holdout_registry,
)
from experiments.r12_high_risk_holdout_transfer_replay import (
    build_r12_high_risk_holdout_transfer_replay,
)
from experiments.r12_recall_oriented_update import (
    build_r12_recall_oriented_update,
)
from experiments.r12_recall_update_false_alarm_stress_test import (
    build_r12_recall_update_false_alarm_stress_test,
)
from experiments.r12_recall_false_alarm_mitigation_candidate import (
    build_r12_recall_false_alarm_mitigation_candidate,
)
from experiments.r12_recall_mitigation_holdout_validation import (
    build_r12_recall_mitigation_holdout_validation,
)
from experiments.r12_recall_mitigation_independent_holdout_data import (
    build_r12_recall_mitigation_independent_holdout_data,
)
from experiments.r12_recall_mitigation_external_holdout_ingestion_or_customer_slice import (
    build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice,
)
from experiments.r12_external_or_customer_holdout_raw_slice import (
    build_r12_external_or_customer_holdout_raw_slice,
)
from experiments.r12_recall_mitigation_external_holdout_revalidation import (
    build_r12_recall_mitigation_external_holdout_revalidation,
)
from experiments.r12_pre_outcome_or_independent_prediction_packet import (
    build_r12_pre_outcome_or_independent_prediction_packet,
)
from experiments.r12_independent_hindcast_revalidation import (
    build_r12_independent_hindcast_revalidation,
)
from experiments.r12_pre_outcome_prediction_trial_or_customer_field_revalidation import (
    build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation,
)
from experiments.r12_pre_outcome_or_customer_field_outcome_ingestion import (
    build_r12_pre_outcome_or_customer_field_outcome_ingestion,
)
from experiments.r12_pre_outcome_or_customer_field_outcome_revalidation import (
    build_r12_pre_outcome_or_customer_field_outcome_revalidation,
)
from experiments.r12_target_outcome_or_customer_field_slice_arrival import (
    build_r12_target_outcome_or_customer_field_slice_arrival,
)
from experiments.r12_customer_field_slice_handoff_package import (
    build_r12_customer_field_slice_handoff_package,
)
from experiments.r12_customer_field_slice_intake_validation import (
    build_r12_customer_field_slice_intake_validation,
)
from experiments.r12_customer_field_slice_revalidation import (
    build_r12_customer_field_slice_revalidation,
)
from experiments.r12_customer_field_outcome_feedback_update import (
    build_r12_customer_field_outcome_feedback_update,
)
from experiments.r12_customer_feedback_update_shadow_replay import (
    build_r12_customer_feedback_update_shadow_replay,
)
from experiments.r12_customer_feedback_shadow_replay_holdout_review import (
    build_r12_customer_feedback_shadow_replay_holdout_review,
)
from experiments.r12_customer_validation_workflow_status import (
    build_r12_customer_validation_workflow_status,
)
from experiments.r12_customer_trial_readiness_package import (
    build_r12_customer_trial_readiness_package,
)
from experiments.r12_customer_trial_operational_check import (
    build_r12_customer_trial_operational_check,
)
from experiments.r12_customer_trial_launch_handoff_package import (
    build_r12_customer_trial_launch_handoff_package,
)
from experiments.r12_customer_trial_launch_packet_export import (
    build_r12_customer_trial_launch_packet_export,
)
from experiments.r12_customer_trial_launch_bundle_verification import (
    build_r12_customer_trial_launch_bundle_verification,
)
from experiments.r12_customer_field_slice_operator_rehearsal import (
    build_r12_customer_field_slice_operator_rehearsal,
)
from experiments.r12_customer_feedback_loop_operator_rehearsal import (
    build_r12_customer_feedback_loop_operator_rehearsal,
)
from experiments.r12_customer_trial_evidence_ledger import (
    build_r12_customer_trial_evidence_ledger,
)


def test_r12_product_support_gate_creates_guarded_transfer_evidence_card():
    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l4-test",
        r12_transfer_validation=_load_current_transfer_validation(),
    )

    assert gate["schema_version"] == R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION
    assert gate["status"] == "r12_product_support_gate_ready_guarded"
    assert gate["claim_level"] == "product_secondary_evidence_only"
    assert gate["product_support_contract"] == {
        "source_backed_only": True,
        "customer_visible_evidence_card_allowed": True,
        "secondary_evidence_card_only": True,
        "customer_visible_primary_claims_use_guarded_baseline": True,
        "r12_can_override_primary_decision": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    card = gate["transfer_evidence_card"]
    assert card["card_id"] == "r12_transfer_validation_evidence_card"
    assert card["claim_status"] == "guarded_transfer_positive_secondary_evidence"
    assert card["display_allowed"] is True
    assert card["primary_decision_allowed"] is False
    assert card["metrics"] == {
        "update_transfer_gain": 0.001287,
        "validation_mean_absolute_error_delta": -0.000431,
        "holdout_mean_absolute_error_delta": -0.000856,
        "interval_coverage_delta": 0.0,
        "false_alarm_rate_delta": 0.0,
    }
    assert card["source_artifact_ids"] == [
        "r12-transfer-validation-current-001",
    ]
    assert card["evidence_summary"]["extended_metric_gates"] == {
        "risk_ranking_non_regression": True,
        "decision_value_non_regression": True,
        "static_prior_miss_recovery_holdout_covered": False,
        "abnormal_segment_recall_holdout_covered": False,
        "extended_product_metric_support_level": (
            "guarded_mae_positive_extended_metric_coverage_gap"
        ),
    }
    assert gate["customer_visible_primary_decision"] == {
        "primary_decision_source": "guarded_baseline_customer_value_report",
        "r12_output_role": "secondary_transfer_evidence_card_only",
        "r12_can_override_primary_decision": False,
        "runtime_default_allowed": False,
    }
    assert gate["acceptance_gates"] == {
        "r12_transfer_positive_guarded": True,
        "customer_visible_evidence_card_allowed": True,
        "secondary_evidence_card_only": True,
        "primary_claims_guarded_baseline_only": True,
        "r12_can_override_primary_decision": False,
        "product_core_method_ready": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "R12 supports Product core method by default" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_preserves_outcome_review_boundary():
    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l4-test",
        r12_transfer_validation=_load_current_transfer_validation(),
    )

    assert gate["outcome_review_handoff"] == {
        "handoff_id": "r12_transfer_evidence_outcome_review",
        "target_artifact_id": "r6-product-outcome-review-current-001",
        "requires_customer_or_field_outcome": True,
        "update_candidate_scope": [
            "mechanism_weight",
            "segment_sensitivity",
            "interaction_edge_weight",
            "uncertainty_parameter",
        ],
        "prompt_or_persona_manual_patch_allowed": False,
        "runtime_default_allowed": False,
    }
    assert gate["source_refs"] == [
        "r12-transfer-validation-current-001",
    ]
    assert gate["source_registry"] == [
        {
            "artifact_id": "r12-transfer-validation-current-001",
            "path": (
                "experiments/results/r12_transfer_validation/"
                "r12-transfer-validation-current-001.json"
            ),
        }
    ]


def test_r12_product_support_gate_surfaces_l5_high_risk_holdout_boundary():
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
    )
    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l5-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_high_risk_holdout_registry=registry,
    )

    high_risk_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "high_risk_holdout_boundary"
    ]
    assert high_risk_boundary == {
        "registry_status": "r12_high_risk_holdout_registry_ready_research_only",
        "research_eligible_case_count": 29,
        "research_recoverable_static_prior_miss_count": 12,
        "product_default_eligible_case_count": 0,
        "product_default_low_sensitive_high_risk_holdout_present": False,
        "product_claim_boundary": (
            "research_only_until_low_sensitive_or_customer_approved_holdout"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_high_risk_research_holdout_candidates_present"
    ] is True
    assert gate["acceptance_gates"][
        "r12_product_default_high_risk_holdout_present"
    ] is False
    assert (
        "R12 Product default high-risk recovery validated"
        in gate["blocked_claims"]
    )
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l6_high_risk_replay_boundary():
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=_load_current_transfer_validation(),
    )
    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l6-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
    )

    replay_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "high_risk_replay_boundary"
    ]
    assert replay_boundary == {
        "replay_status": (
            "r12_high_risk_holdout_transfer_replay_partial_research_positive"
        ),
        "transfer_decision": (
            "r12_high_risk_replay_mae_positive_recall_flat_research_only"
        ),
        "mean_absolute_error_delta": -0.003684,
        "static_prior_miss_recovery_delta": 0.0,
        "abnormal_segment_recall_delta": 0.0,
        "product_support_level": (
            "research_only_mae_positive_recall_and_product_default_gap"
        ),
        "product_default_eligible_high_risk_holdout_present": False,
    }
    assert gate["acceptance_gates"]["r12_high_risk_replay_mae_improved"] is True
    assert (
        gate["acceptance_gates"]["r12_high_risk_replay_recall_improved"] is False
    )
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
    }
    assert (
        "static-prior miss recovery improved on high-risk replay"
        in gate["blocked_claims"]
    )
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l7_recall_oriented_update_boundary():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l7-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
    )

    recall_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "recall_oriented_update_boundary"
    ]
    assert recall_boundary == {
        "update_status": "r12_recall_oriented_update_ready_research_guarded",
        "acceptance_decision": (
            "research_guarded_recall_candidate_accept_false_alarm_tradeoff"
        ),
        "recommended_activation_margin": 0.01,
        "static_prior_miss_recovery_delta": 0.206897,
        "abnormal_segment_recall_delta": 0.206897,
        "false_alarm_rate_delta": 0.073171,
        "precision_delta": -0.03,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_recall_update_holdout_false_alarm_stress_test"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_recall_oriented_update_recall_improved"
    ] is True
    assert gate["acceptance_gates"][
        "r12_recall_oriented_update_false_alarm_non_regression"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_oriented_update_product_default_allowed"
    ] is False
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
    }
    assert "false_alarm_non_regression=true" in gate["blocked_claims"]
    assert "precision_non_regression=true" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_customer_field_slice_operator_rehearsal_boundary(
    tmp_path,
):
    rehearsal = build_r12_customer_field_slice_operator_rehearsal(
        artifact_id="r12-customer-field-slice-operator-rehearsal-test",
        run_id="r12-l34-product-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_handoff_package_path=_current_l21_path(),
        rehearsal_started_at="2026-06-28T11:30:00Z",
        rehearsal_work_dir=tmp_path / "operator-rehearsal",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l34-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_field_slice_operator_rehearsal=rehearsal,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_field_slice_operator_rehearsal_boundary"
    ]
    assert boundary == {
        "operator_rehearsal_status": (
            "r12_customer_field_slice_operator_rehearsal_ready_no_field_claim"
        ),
        "sample_slice_kind": "synthetic_rehearsal_fixture",
        "operator_command_rehearsed": True,
        "sample_slice_ready_for_revalidation": True,
        "real_customer_field_slice_submitted": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "real_customer_field_slice_intake_validation_or_target_outcome_revalidation"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_operator_rehearsed"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_operator_real_customer_slice_submitted"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_operator_product_default_allowed"
    ] is False
    assert "r12-customer-field-slice-operator-rehearsal-test" in gate[
        "source_refs"
    ]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } >= {
        "r12-transfer-validation-current-001",
        "r12-customer-field-slice-operator-rehearsal-test",
    }
    assert "real_customer_field_slice_validated=true" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_customer_feedback_loop_operator_rehearsal_boundary(
    tmp_path,
):
    rehearsal = build_r12_customer_feedback_loop_operator_rehearsal(
        artifact_id="r12-customer-feedback-loop-operator-rehearsal-test",
        run_id="r12-l35-product-test",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_handoff_package_path=_current_l21_path(),
        rehearsal_started_at="2026-06-28T12:20:00Z",
        rehearsal_work_dir=tmp_path / "feedback-loop-rehearsal",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l35-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_feedback_loop_operator_rehearsal=rehearsal,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_feedback_loop_operator_rehearsal_boundary"
    ]
    assert boundary == {
        "feedback_loop_rehearsal_status": (
            "r12_customer_feedback_loop_operator_rehearsal_ready_no_field_claim"
        ),
        "sample_slice_kind": "synthetic_feedback_loop_rehearsal_fixture",
        "l22_intake_validator_executed": True,
        "l23_field_revalidation_executed": True,
        "l24_feedback_candidates_generated": True,
        "l25_shadow_replay_executed": True,
        "l26_synthetic_holdout_review_executed": True,
        "real_customer_field_slice_submitted": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": "real_customer_field_slice_or_public_target_outcome",
    }
    assert gate["acceptance_gates"][
        "r12_customer_feedback_loop_rehearsed_l22_to_l26"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_feedback_loop_real_customer_slice_submitted"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_feedback_loop_product_default_allowed"
    ] is False
    assert "r12-customer-feedback-loop-operator-rehearsal-test" in gate[
        "source_refs"
    ]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } >= {
        "r12-transfer-validation-current-001",
        "r12-customer-feedback-loop-operator-rehearsal-test",
    }
    assert "real_customer_field_slice_validated=true" in gate["blocked_claims"]
    assert "metrics_computed_on_real_customer_slice=true" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_customer_trial_evidence_ledger_boundary():
    ledger = build_r12_customer_trial_evidence_ledger(
        artifact_id="r12-customer-trial-evidence-ledger-test",
        run_id="r12-l36-product-test",
        ledger_created_at="2026-06-28T16:10:00Z",
        r12_customer_trial_launch_bundle_verification=_load_current_l32(),
        r12_customer_trial_launch_bundle_verification_path=_current_l32_path(),
        r12_customer_field_slice_operator_rehearsal=_load_current_l34(),
        r12_customer_field_slice_operator_rehearsal_path=_current_l34_path(),
        r12_customer_feedback_loop_operator_rehearsal=_load_current_l35(),
        r12_customer_feedback_loop_operator_rehearsal_path=_current_l35_path(),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l36-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_trial_evidence_ledger=ledger,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_evidence_ledger_boundary"
    ]
    assert boundary == {
        "ledger_status": "r12_customer_trial_evidence_ledger_ready_source_pending",
        "launch_bundle_verified": True,
        "operator_rehearsal_executed": True,
        "feedback_loop_rehearsed_l22_to_l26": True,
        "customer_visible_readiness_evidence_count": 1,
        "operator_only_rehearsal_evidence_count": 2,
        "blocking_gap_count": 3,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": "real_customer_field_slice_or_public_target_outcome",
    }
    assert gate["acceptance_gates"][
        "r12_customer_trial_evidence_ledger_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_trial_evidence_ledger_field_outcome_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_trial_evidence_ledger_product_default_allowed"
    ] is False
    assert "r12-customer-trial-evidence-ledger-test" in gate["source_refs"]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } >= {
        "r12-transfer-validation-current-001",
        "r12-customer-trial-evidence-ledger-test",
    }
    assert "metrics_computed_on_real_customer_slice=true" in gate[
        "blocked_claims"
    ]
    assert "runtime_default_allowed=true" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l8_false_alarm_stress_boundary():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l8-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )

    stress_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "recall_false_alarm_stress_boundary"
    ]
    assert stress_boundary == {
        "stress_status": (
            "r12_recall_update_false_alarm_stress_blocked_product_default"
        ),
        "acceptance_decision": (
            "reject_product_default_keep_research_guarded_candidate"
        ),
        "global_recall_delta": 0.206897,
        "global_false_alarm_rate_delta": 0.073171,
        "precision_delta": -0.03,
        "low_sensitive_recall_evaluable": False,
        "low_sensitive_false_alarm_rate_delta": 0.0,
        "protected_sensitive_false_alarm_rate_delta": 0.096774,
        "dominant_false_alarm_segment_column": "TAGE",
        "product_default_allowed": False,
        "next_required_artifact": "r12_recall_false_alarm_mitigation_candidate",
    }
    assert gate["acceptance_gates"][
        "r12_recall_false_alarm_stress_passed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_false_alarm_stress_product_default_allowed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_false_alarm_stress_sensitive_concentration"
    ] is True
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
    }
    assert (
        "r12 recall update false-alarm stress passed"
        in gate["blocked_claims"]
    )
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l9_false_alarm_mitigation_boundary():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l9-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )

    mitigation_boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "recall_false_alarm_mitigation_boundary"
    ]
    assert mitigation_boundary == {
        "mitigation_status": (
            "r12_recall_false_alarm_mitigation_ready_research_guarded"
        ),
        "acceptance_decision": (
            "accept_research_guarded_mitigation_reject_product_default"
        ),
        "candidate_id": "r12-tage-58-62-activation-guard-001",
        "target_segment_column": "TAGE",
        "target_segment_value_min": 58,
        "target_segment_value_max": 62,
        "mitigated_recall_delta": 0.172414,
        "l7_recall_gain_retained": 0.833333,
        "mitigated_false_alarm_rate_delta": 0.0,
        "mitigated_precision_delta": 0.059524,
        "overfit_risk": "high_current_false_alarm_band_derived",
        "product_default_allowed": False,
        "next_required_artifact": "r12_recall_mitigation_holdout_validation",
    }
    assert gate["acceptance_gates"][
        "r12_recall_false_alarm_mitigation_selected"
    ] is True
    assert gate["acceptance_gates"][
        "r12_recall_false_alarm_mitigation_false_alarm_non_regression"
    ] is True
    assert gate["acceptance_gates"][
        "r12_recall_false_alarm_mitigation_product_default_allowed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_false_alarm_mitigation_overfit_risk_present"
    ] is True
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
    }
    assert (
        "mitigation generalizes beyond current false-alarm band"
        in gate["blocked_claims"]
    )
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l10_mitigation_holdout_boundary():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )
    holdout_validation = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l10-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
        r12_recall_mitigation_holdout_validation=holdout_validation,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "recall_mitigation_holdout_validation_boundary"
    ]
    assert boundary == {
        "validation_status": (
            "r12_recall_mitigation_holdout_validation_blocked_overfit"
        ),
        "acceptance_decision": (
            "reject_product_default_retain_as_failure_diagnosis_candidate"
        ),
        "leave_one_pass_rate": 0.333333,
        "endpoint_holdout_failure_count": 2,
        "independent_holdout_present": False,
        "low_sensitive_recall_evaluable": False,
        "stable_alternative_recall_retained": 0.333333,
        "mitigation_holdout_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": "r12_recall_mitigation_independent_holdout_data",
    }
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_holdout_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_holdout_product_default_allowed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_holdout_independent_present"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_holdout_leave_one_stable"
    ] is False
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
    }
    assert "mitigation holdout validated" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l11_independent_holdout_data_boundary():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )
    holdout_validation = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )
    independent_data = build_r12_recall_mitigation_independent_holdout_data(
        artifact_id="r12-recall-mitigation-independent-holdout-data-test",
        run_id="r12-l11-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r10_external_evidence_registry=_load_current_external_registry(),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l11-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r12_recall_mitigation_independent_holdout_data=independent_data,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "recall_mitigation_independent_holdout_data_boundary"
    ]
    assert boundary == {
        "data_status": (
            "r12_recall_mitigation_independent_holdout_data_blocked_needs_external_or_customer_slice"
        ),
        "acceptance_decision": (
            "block_product_default_prepare_external_or_customer_holdout_ingestion"
        ),
        "same_dataset_non_derivation_recall_candidate_count": 5,
        "low_sensitive_observed_high_risk_count": 0,
        "external_registry_candidate_count": 3,
        "ingested_external_independent_dataset_count": 0,
        "mitigation_independent_data_ready": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_independent_data_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_independent_external_data_ingested"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_independent_low_sensitive_recall_evaluable"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_independent_product_default_allowed"
    ] is False
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
    }
    assert "independent holdout data exists" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l12_external_or_customer_slice_contract():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )
    holdout_validation = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )
    independent_data = build_r12_recall_mitigation_independent_holdout_data(
        artifact_id="r12-recall-mitigation-independent-holdout-data-test",
        run_id="r12-l11-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r10_external_evidence_registry=_load_current_external_registry(),
    )
    external_or_customer_slice = (
        build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            artifact_id=(
                "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
            ),
            run_id="r12-l12-test",
            r12_recall_mitigation_independent_holdout_data=independent_data,
            r10_external_evidence_registry=_load_current_external_registry(),
        )
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l12-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r12_recall_mitigation_independent_holdout_data=independent_data,
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_slice
        ),
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary"
    ]
    assert boundary == {
        "contract_status": (
            "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice_ready_contract_blocked_no_raw_slice"
        ),
        "selected_route": "external_public_holdout_first_customer_slice_compatible",
        "preferred_external_source_id": (
            "dot_air_travel_consumer_report_complaint_candidate"
        ),
        "customer_slice_fallback_enabled": True,
        "raw_external_or_customer_slice_present": False,
        "minimum_case_count_met": False,
        "customer_approval_present": False,
        "product_default_allowed": False,
        "next_required_artifact": "r12_external_or_customer_holdout_raw_slice",
    }
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_external_or_customer_contract_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_external_or_customer_raw_slice_present"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_external_or_customer_revalidation_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_external_or_customer_product_default_allowed"
    ] is False
    assert "raw external or customer holdout slice present" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l13_raw_slice_and_keeps_revalidation_blocked():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )
    holdout_validation = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )
    independent_data = build_r12_recall_mitigation_independent_holdout_data(
        artifact_id="r12-recall-mitigation-independent-holdout-data-test",
        run_id="r12-l11-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r10_external_evidence_registry=_load_current_external_registry(),
    )
    external_or_customer_contract = (
        build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            artifact_id=(
                "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
            ),
            run_id="r12-l12-test",
            r12_recall_mitigation_independent_holdout_data=independent_data,
            r10_external_evidence_registry=_load_current_external_registry(),
        )
    )
    raw_slice = build_r12_external_or_customer_holdout_raw_slice(
        artifact_id="r12-external-or-customer-holdout-raw-slice-test",
        run_id="r12-l13-test",
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_contract
        ),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l13-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r12_recall_mitigation_independent_holdout_data=independent_data,
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_contract
        ),
        r12_external_or_customer_holdout_raw_slice=raw_slice,
    )

    summary = gate["transfer_evidence_card"]["evidence_summary"]
    raw_boundary = summary["external_or_customer_holdout_raw_slice_boundary"]
    assert raw_boundary == {
        "raw_slice_status": (
            "r12_external_or_customer_holdout_raw_slice_ready_external_dot_atcr_revalidation_pending"
        ),
        "selected_source_id": "dot_air_travel_consumer_report_complaint_candidate",
        "case_count": 14,
        "source_row_count": 15,
        "total_observed_complaint_cases": 4839,
        "actual_public_data_ingested": True,
        "prediction_fields_present": False,
        "external_holdout_revalidation_ready": False,
        "product_default_allowed": False,
        "next_required_artifact": "r12_recall_mitigation_external_holdout_revalidation",
    }
    contract_boundary = summary[
        "recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary"
    ]
    assert contract_boundary["raw_external_or_customer_slice_present"] is True
    assert gate["acceptance_gates"][
        "r12_external_or_customer_raw_slice_present"
    ] is True
    assert gate["acceptance_gates"][
        "r12_recall_mitigation_external_or_customer_raw_slice_present"
    ] is True
    assert gate["acceptance_gates"][
        "r12_external_or_customer_actual_public_data_ingested"
    ] is True
    assert gate["acceptance_gates"][
        "r12_external_or_customer_revalidation_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_external_or_customer_product_default_allowed"
    ] is False
    assert "raw external or customer holdout slice present" not in gate["blocked_claims"]
    assert "external holdout revalidation completed" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l14_external_revalidation_boundary():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )
    holdout_validation = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )
    independent_data = build_r12_recall_mitigation_independent_holdout_data(
        artifact_id="r12-recall-mitigation-independent-holdout-data-test",
        run_id="r12-l11-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r10_external_evidence_registry=_load_current_external_registry(),
    )
    external_or_customer_contract = (
        build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            artifact_id=(
                "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
            ),
            run_id="r12-l12-test",
            r12_recall_mitigation_independent_holdout_data=independent_data,
            r10_external_evidence_registry=_load_current_external_registry(),
        )
    )
    raw_slice = build_r12_external_or_customer_holdout_raw_slice(
        artifact_id="r12-external-or-customer-holdout-raw-slice-test",
        run_id="r12-l13-test",
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_contract
        ),
    )
    revalidation = build_r12_recall_mitigation_external_holdout_revalidation(
        artifact_id="r12-recall-mitigation-external-holdout-revalidation-test",
        run_id="r12-l14-test",
        r12_external_or_customer_holdout_raw_slice=raw_slice,
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l14-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r12_recall_mitigation_independent_holdout_data=independent_data,
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_contract
        ),
        r12_external_or_customer_holdout_raw_slice=raw_slice,
        r12_recall_mitigation_external_holdout_revalidation=revalidation,
    )

    summary = gate["transfer_evidence_card"]["evidence_summary"]
    boundary = summary["recall_mitigation_external_holdout_revalidation_boundary"]
    assert boundary == {
        "revalidation_status": (
            "r12_recall_mitigation_external_holdout_revalidation_blocked_prediction_proxy_only"
        ),
        "acceptance_decision": (
            "reject_product_default_keep_as_proxy_external_revalidation_diagnostic"
        ),
        "case_count": 14,
        "mean_absolute_error_delta": -0.004329,
        "interval_coverage_delta": 0.071429,
        "risk_ranking_quality_delta": 0.25,
        "static_prior_miss_recovery_delta": 0.8,
        "false_alarm_rate_delta": 0.428571,
        "prediction_source_independent_of_observed_outcome": False,
        "same_table_prediction_leakage_risk": True,
        "external_holdout_revalidation_passed": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_pre_outcome_or_independent_prediction_packet"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_external_holdout_revalidation_executed"
    ] is True
    assert gate["acceptance_gates"][
        "r12_external_holdout_revalidation_passed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_external_holdout_prediction_independent"
    ] is False
    assert gate["acceptance_gates"][
        "r12_external_holdout_false_alarm_non_regression"
    ] is False
    assert gate["acceptance_gates"][
        "r12_external_holdout_product_default_allowed"
    ] is False
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
    }
    assert "external holdout revalidation completed" not in gate["blocked_claims"]
    assert (
        "external holdout revalidation passed with independent predictions"
        in gate["blocked_claims"]
    )
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l15_prediction_packet_boundary():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )
    holdout_validation = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )
    independent_data = build_r12_recall_mitigation_independent_holdout_data(
        artifact_id="r12-recall-mitigation-independent-holdout-data-test",
        run_id="r12-l11-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r10_external_evidence_registry=_load_current_external_registry(),
    )
    external_or_customer_contract = (
        build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            artifact_id=(
                "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
            ),
            run_id="r12-l12-test",
            r12_recall_mitigation_independent_holdout_data=independent_data,
            r10_external_evidence_registry=_load_current_external_registry(),
        )
    )
    raw_slice = build_r12_external_or_customer_holdout_raw_slice(
        artifact_id="r12-external-or-customer-holdout-raw-slice-test",
        run_id="r12-l13-test",
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_contract
        ),
    )
    revalidation = build_r12_recall_mitigation_external_holdout_revalidation(
        artifact_id="r12-recall-mitigation-external-holdout-revalidation-test",
        run_id="r12-l14-test",
        r12_external_or_customer_holdout_raw_slice=raw_slice,
    )
    packet = build_r12_pre_outcome_or_independent_prediction_packet(
        artifact_id="r12-pre-outcome-or-independent-prediction-packet-test",
        run_id="r12-l15-test",
        r12_recall_mitigation_external_holdout_revalidation=revalidation,
        r12_external_or_customer_holdout_raw_slice=raw_slice,
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l15-product-test",
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_registry=registry,
        r12_high_risk_holdout_transfer_replay=replay,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r12_recall_mitigation_independent_holdout_data=independent_data,
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_contract
        ),
        r12_external_or_customer_holdout_raw_slice=raw_slice,
        r12_recall_mitigation_external_holdout_revalidation=revalidation,
        r12_pre_outcome_or_independent_prediction_packet=packet,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "pre_outcome_or_independent_prediction_packet_boundary"
    ]
    assert boundary == {
        "packet_status": (
            "r12_pre_outcome_or_independent_prediction_packet_ready_independent_hindcast_not_pre_registered"
        ),
        "acceptance_decision": (
            "accept_independent_hindcast_prediction_packet_block_pre_outcome_and_product_default"
        ),
        "prediction_route": "prior_month_complaint_share_hindcast",
        "prediction_case_count": 14,
        "matched_case_count": 14,
        "prediction_source_independent_of_target_outcome": True,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "same_table_prediction_leakage_risk": False,
        "hindcast_independent_revalidation_ready": True,
        "pre_outcome_revalidation_ready": False,
        "product_default_allowed": False,
        "next_required_artifact": "r12_independent_hindcast_revalidation",
    }
    assert gate["acceptance_gates"][
        "r12_pre_outcome_or_independent_prediction_packet_generated"
    ] is True
    assert gate["acceptance_gates"][
        "r12_prediction_source_independent_of_target_outcome"
    ] is True
    assert gate["acceptance_gates"][
        "r12_prediction_lock_timestamp_pre_target_outcome"
    ] is False
    assert gate["acceptance_gates"][
        "r12_hindcast_independent_revalidation_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_pre_outcome_revalidation_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_pre_outcome_or_independent_prediction_product_default_allowed"
    ] is False
    assert "pre-outcome prediction packet locked before target outcome" in gate[
        "blocked_claims"
    ]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
        "r12-pre-outcome-or-independent-prediction-packet-test",
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l16_independent_hindcast_boundary():
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l16-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "independent_hindcast_revalidation_boundary"
    ]
    assert boundary == {
        "hindcast_status": (
            "r12_independent_hindcast_revalidation_passed_guarded_not_pre_outcome"
        ),
        "acceptance_decision": (
            "accept_independent_hindcast_positive_keep_product_default_blocked_until_pre_outcome_or_field_validation"
        ),
        "case_count": 14,
        "mean_absolute_error_delta": -0.062951,
        "interval_coverage_delta": 0.714286,
        "risk_ranking_quality_delta": 1.0,
        "static_prior_miss_recovery_delta": 1.0,
        "false_alarm_rate_delta": 0.0,
        "decision_value_delta": 0.714286,
        "prediction_source_independent_of_target_outcome": True,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "hindcast_independent_revalidation_passed": True,
        "pre_outcome_revalidation_ready": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_pre_outcome_prediction_trial_or_customer_field_revalidation"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_independent_hindcast_revalidation_executed"
    ] is True
    assert gate["acceptance_gates"][
        "r12_independent_hindcast_revalidation_passed"
    ] is True
    assert gate["acceptance_gates"][
        "r12_independent_hindcast_false_alarm_non_regression"
    ] is True
    assert gate["acceptance_gates"][
        "r12_independent_hindcast_pre_outcome_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_independent_hindcast_product_default_allowed"
    ] is False
    assert "pre-outcome validation passed" in gate["blocked_claims"]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
        "r12-pre-outcome-or-independent-prediction-packet-test",
        "r12-independent-hindcast-revalidation-test",
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_allows_guarded_public_data_effectiveness_claim():
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-public-data-stage-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-public-data-stage-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
    )

    assert gate["public_data_validation_scope"] == {
        "stage": "public_data_validation_only",
        "public_data_effectiveness_claim_allowed": True,
        "public_data_effectiveness_claim": (
            "tested_effective_on_public_data_guarded"
        ),
        "customer_field_validation_required_for_current_stage": False,
        "customer_field_validation_claim_allowed": False,
        "runtime_default_allowed": False,
        "required_public_evidence": [
            "r12_transfer_validation",
            "r12_external_or_customer_holdout_raw_slice",
            "r12_pre_outcome_or_independent_prediction_packet",
            "r12_independent_hindcast_revalidation",
        ],
        "validated_public_metrics": [
            "mean_absolute_error_delta",
            "interval_coverage_delta",
            "risk_ranking_quality_delta",
            "static_prior_miss_recovery_delta",
            "false_alarm_rate_delta",
            "decision_value_delta",
        ],
    }
    assert gate["product_support_contract"][
        "public_data_effectiveness_claim_allowed"
    ] is True
    assert gate["acceptance_gates"][
        "r12_public_data_effectiveness_claim_allowed"
    ] is True
    assert gate["acceptance_gates"][
        "customer_field_validation_required_for_current_stage"
    ] is False
    assert (
        "R12 has tested effective on public data under guarded hindcast metrics."
        in gate["allowed_claims"]
    )
    assert "customer field outcome validated" in gate["blocked_claims"]
    assert "runtime_default_allowed=true" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l17_pre_outcome_trial_boundary():
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l17-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "pre_outcome_prediction_trial_or_customer_field_revalidation_boundary"
    ]
    assert boundary == {
        "trial_status": (
            "r12_pre_outcome_prediction_trial_locked_outcome_pending_guarded"
        ),
        "acceptance_decision": (
            "accept_pre_outcome_trial_lock_keep_validation_and_product_default_blocked_until_outcome_ingestion"
        ),
        "selected_route": "pre_outcome_public_dot_trial",
        "prediction_lock_timestamp": "2026-06-27T14:45:00Z",
        "feature_period": "April 2026",
        "target_outcome_period": "May 2026",
        "prediction_case_count": 14,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "target_outcome_artifact_present": False,
        "pre_outcome_revalidation_ready": False,
        "customer_field_slice_contract_ready": True,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_ingestion"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_pre_outcome_prediction_trial_created"
    ] is True
    assert gate["acceptance_gates"][
        "r12_pre_outcome_prediction_packet_locked"
    ] is True
    assert gate["acceptance_gates"][
        "r12_pre_outcome_prediction_lock_pre_target_outcome"
    ] is True
    assert gate["acceptance_gates"][
        "r12_pre_outcome_target_outcome_artifact_present"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_contract_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_pre_outcome_or_customer_field_product_default_allowed"
    ] is False
    assert "pre-outcome outcome revalidation passed" in gate["blocked_claims"]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
        "r12-pre-outcome-or-independent-prediction-packet-test",
        "r12-independent-hindcast-revalidation-test",
        (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l18_outcome_ingestion_pending_boundary():
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )
    ingestion = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        availability_checked_at="2026-06-27T14:55:00Z",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l18-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "pre_outcome_or_customer_field_outcome_ingestion_boundary"
    ]
    assert boundary == {
        "ingestion_status": (
            "r12_pre_outcome_or_customer_field_outcome_ingestion_pending_no_target_outcome"
        ),
        "acceptance_decision": (
            "accept_outcome_ingestion_pending_keep_validation_and_product_default_blocked"
        ),
        "target_outcome_period": "May 2026",
        "availability_checked_at": "2026-06-27T14:55:00Z",
        "latest_available_report": (
            "June 2026 Air Travel Consumer Report (April 2026 Data)"
        ),
        "target_public_outcome_available": False,
        "target_outcome_artifact_present": False,
        "customer_field_slice_contract_ready": True,
        "customer_field_slice_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_revalidation"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_outcome_ingestion_target_public_outcome_available"
    ] is False
    assert gate["acceptance_gates"][
        "r12_outcome_ingestion_target_outcome_artifact_present"
    ] is False
    assert gate["acceptance_gates"][
        "r12_outcome_ingestion_customer_field_slice_contract_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_outcome_ingestion_revalidation_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_outcome_ingestion_product_default_allowed"
    ] is False
    assert "target outcome artifact present" in gate["blocked_claims"]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
        "r12-pre-outcome-or-independent-prediction-packet-test",
        "r12-independent-hindcast-revalidation-test",
        (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        "r12-pre-outcome-or-customer-field-outcome-ingestion-test",
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l19_fail_closed_outcome_revalidation_boundary():
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )
    ingestion = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        availability_checked_at="2026-06-27T14:55:00Z",
    )
    revalidation = (
        build_r12_pre_outcome_or_customer_field_outcome_revalidation(
            artifact_id=(
                "r12-pre-outcome-or-customer-field-outcome-revalidation-test"
            ),
            run_id="r12-l19-test",
            r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
            revalidation_requested_at="2026-06-27T15:05:00Z",
        )
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l19-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "pre_outcome_or_customer_field_outcome_revalidation_boundary"
    ]
    assert boundary == {
        "revalidation_status": (
            "r12_pre_outcome_or_customer_field_outcome_revalidation_blocked_no_outcome"
        ),
        "acceptance_decision": (
            "reject_revalidation_without_outcome_keep_product_default_blocked"
        ),
        "target_outcome_period": "May 2026",
        "metrics_computed": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "field_or_pre_outcome_revalidation_passed": False,
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_target_outcome_or_customer_field_slice_arrival"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_outcome_revalidation_metrics_computed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_outcome_revalidation_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_outcome_revalidation_passed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_outcome_revalidation_product_default_allowed"
    ] is False
    assert "field_or_pre_outcome_revalidation_passed=true" in gate[
        "blocked_claims"
    ]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
        "r12-pre-outcome-or-independent-prediction-packet-test",
        "r12-independent-hindcast-revalidation-test",
        (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        "r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        "r12-pre-outcome-or-customer-field-outcome-revalidation-test",
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l20_target_or_customer_slice_arrival_boundary():
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )
    ingestion = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        availability_checked_at="2026-06-27T14:55:00Z",
    )
    revalidation = (
        build_r12_pre_outcome_or_customer_field_outcome_revalidation(
            artifact_id=(
                "r12-pre-outcome-or-customer-field-outcome-revalidation-test"
            ),
            run_id="r12-l19-test",
            r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
            revalidation_requested_at="2026-06-27T15:05:00Z",
        )
    )
    arrival = build_r12_target_outcome_or_customer_field_slice_arrival(
        artifact_id="r12-target-outcome-or-customer-field-slice-arrival-test",
        run_id="r12-l20-test",
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        arrival_checked_at="2026-06-27T15:30:00Z",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l20-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "target_outcome_or_customer_field_slice_arrival_boundary"
    ]
    assert boundary == {
        "arrival_status": (
            "r12_target_outcome_or_customer_field_slice_arrival_pending_no_source"
        ),
        "acceptance_decision": (
            "keep_waiting_for_target_outcome_or_customer_field_slice"
        ),
        "target_outcome_period": "May 2026",
        "outcome_source_arrived": False,
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "metrics_computed": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_target_outcome_or_customer_field_slice_arrival"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_target_or_customer_slice_arrival_source_arrived"
    ] is False
    assert gate["acceptance_gates"][
        "r12_target_or_customer_slice_arrival_revalidation_ready"
    ] is False
    assert gate["acceptance_gates"][
        "r12_target_or_customer_slice_arrival_metrics_computed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_target_or_customer_slice_arrival_product_default_allowed"
    ] is False
    assert "outcome_source_arrived=true" in gate["blocked_claims"]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
        "r12-pre-outcome-or-independent-prediction-packet-test",
        "r12-independent-hindcast-revalidation-test",
        (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        "r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        "r12-pre-outcome-or-customer-field-outcome-revalidation-test",
        "r12-target-outcome-or-customer-field-slice-arrival-test",
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l21_customer_field_slice_handoff_package_boundary():
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )
    ingestion = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        availability_checked_at="2026-06-27T14:55:00Z",
    )
    revalidation = (
        build_r12_pre_outcome_or_customer_field_outcome_revalidation(
            artifact_id=(
                "r12-pre-outcome-or-customer-field-outcome-revalidation-test"
            ),
            run_id="r12-l19-test",
            r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
            revalidation_requested_at="2026-06-27T15:05:00Z",
        )
    )
    arrival = build_r12_target_outcome_or_customer_field_slice_arrival(
        artifact_id="r12-target-outcome-or-customer-field-slice-arrival-test",
        run_id="r12-l20-test",
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        arrival_checked_at="2026-06-27T15:30:00Z",
    )
    handoff = build_r12_customer_field_slice_handoff_package(
        artifact_id="r12-customer-field-slice-handoff-package-test",
        run_id="r12-l21-test",
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        generated_at="2026-06-27T15:45:00Z",
        template_output_path=(
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l21-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        r12_customer_field_slice_handoff_package=handoff,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_field_slice_handoff_package_boundary"
    ]
    assert boundary == {
        "handoff_status": (
            "r12_customer_field_slice_handoff_package_ready_guarded"
        ),
        "acceptance_decision": (
            "accept_customer_field_slice_handoff_ready_keep_validation_blocked"
        ),
        "target_outcome_period": "May 2026",
        "minimum_case_count": 10,
        "template_output_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
        "customer_data_request_ready": True,
        "customer_field_slice_contract_machine_checkable": True,
        "metrics_computed": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_target_outcome_or_customer_field_slice_arrival_with_customer_slice"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_handoff_template_generated"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_handoff_data_request_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_handoff_metrics_computed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_handoff_product_default_allowed"
    ] is False
    assert "direct personal identifiers in customer slice" in gate[
        "blocked_claims"
    ]
    assert {
        entry["artifact_id"] for entry in gate["source_registry"]
    } == {
        "r12-transfer-validation-current-001",
        "r12-high-risk-holdout-registry-test",
        "r12-high-risk-holdout-transfer-replay-test",
        "r12-recall-oriented-update-test",
        "r12-recall-update-false-alarm-stress-test",
        "r12-recall-false-alarm-mitigation-candidate-test",
        "r12-recall-mitigation-holdout-validation-test",
        "r12-recall-mitigation-independent-holdout-data-test",
        (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        "r12-external-or-customer-holdout-raw-slice-test",
        "r12-recall-mitigation-external-holdout-revalidation-test",
        "r12-pre-outcome-or-independent-prediction-packet-test",
        "r12-independent-hindcast-revalidation-test",
        (
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        "r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        "r12-pre-outcome-or-customer-field-outcome-revalidation-test",
        "r12-target-outcome-or-customer-field-slice-arrival-test",
        "r12-customer-field-slice-handoff-package-test",
    }
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l22_customer_field_slice_intake_validation_boundary(
    tmp_path,
):
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )
    ingestion = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        availability_checked_at="2026-06-27T14:55:00Z",
    )
    revalidation = (
        build_r12_pre_outcome_or_customer_field_outcome_revalidation(
            artifact_id=(
                "r12-pre-outcome-or-customer-field-outcome-revalidation-test"
            ),
            run_id="r12-l19-test",
            r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
            revalidation_requested_at="2026-06-27T15:05:00Z",
        )
    )
    arrival = build_r12_target_outcome_or_customer_field_slice_arrival(
        artifact_id="r12-target-outcome-or-customer-field-slice-arrival-test",
        run_id="r12-l20-test",
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        arrival_checked_at="2026-06-27T15:30:00Z",
    )
    handoff = build_r12_customer_field_slice_handoff_package(
        artifact_id="r12-customer-field-slice-handoff-package-test",
        run_id="r12-l21-test",
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        generated_at="2026-06-27T15:45:00Z",
        template_output_path=(
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
    )
    customer_slice = tmp_path / "customer-field-slice.csv"
    _write_valid_customer_slice(customer_slice)
    intake = build_r12_customer_field_slice_intake_validation(
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=handoff,
        intake_checked_at="2026-06-27T16:05:00Z",
        customer_field_slice_path=customer_slice,
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l22-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        r12_customer_field_slice_handoff_package=handoff,
        r12_customer_field_slice_intake_validation=intake,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_field_slice_intake_validation_boundary"
    ]
    assert boundary == {
        "intake_status": (
            "r12_customer_field_slice_intake_validation_ready_for_revalidation_guarded"
        ),
        "acceptance_decision": (
            "accept_customer_field_slice_intake_enable_revalidation_not_product_default"
        ),
        "case_count": 10,
        "minimum_case_count": 10,
        "ready_for_revalidation": True,
        "privacy_valid": True,
        "numeric_fields_valid": True,
        "timestamps_valid": True,
        "duplicate_case_ids_absent": True,
        "metrics_computed": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_revalidation_with_customer_slice"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_intake_ready_for_revalidation"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_intake_metrics_computed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_intake_product_default_allowed"
    ] is False
    assert "r12-customer-field-slice-intake-validation-test" in gate[
        "source_refs"
    ]
    assert "field_outcome_validated=true" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l23_customer_field_slice_revalidation_boundary(
    tmp_path,
):
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )
    ingestion = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        availability_checked_at="2026-06-27T14:55:00Z",
    )
    revalidation = (
        build_r12_pre_outcome_or_customer_field_outcome_revalidation(
            artifact_id=(
                "r12-pre-outcome-or-customer-field-outcome-revalidation-test"
            ),
            run_id="r12-l19-test",
            r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
            revalidation_requested_at="2026-06-27T15:05:00Z",
        )
    )
    arrival = build_r12_target_outcome_or_customer_field_slice_arrival(
        artifact_id="r12-target-outcome-or-customer-field-slice-arrival-test",
        run_id="r12-l20-test",
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        arrival_checked_at="2026-06-27T15:30:00Z",
    )
    handoff = build_r12_customer_field_slice_handoff_package(
        artifact_id="r12-customer-field-slice-handoff-package-test",
        run_id="r12-l21-test",
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        generated_at="2026-06-27T15:45:00Z",
        template_output_path=(
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
    )
    customer_slice = tmp_path / "customer-field-slice.csv"
    _write_valid_customer_slice(customer_slice)
    intake = build_r12_customer_field_slice_intake_validation(
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=handoff,
        intake_checked_at="2026-06-28T09:00:00Z",
        customer_field_slice_path=customer_slice,
    )
    customer_revalidation = build_r12_customer_field_slice_revalidation(
        artifact_id="r12-customer-field-slice-revalidation-test",
        run_id="r12-l23-test",
        r12_customer_field_slice_intake_validation=intake,
        revalidation_checked_at="2026-06-28T09:15:00Z",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l23-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        r12_customer_field_slice_handoff_package=handoff,
        r12_customer_field_slice_intake_validation=intake,
        r12_customer_field_slice_revalidation=customer_revalidation,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_field_slice_revalidation_boundary"
    ]
    assert boundary == {
        "revalidation_status": (
            "r12_customer_field_slice_revalidation_metrics_ready_guarded"
        ),
        "acceptance_decision": (
            "accept_customer_field_revalidation_metrics_keep_product_default_blocked"
        ),
        "case_count": 10,
        "metrics_computed": True,
        "field_outcome_validated": True,
        "mean_absolute_error": 0.02,
        "risk_ranking_quality": 1.0,
        "product_default_allowed": False,
        "next_required_artifact": "r12_customer_field_outcome_feedback_update",
    }
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_revalidation_metrics_computed"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_revalidation_field_outcome_validated"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_field_slice_revalidation_product_default_allowed"
    ] is False
    assert "r12-customer-field-slice-revalidation-test" in gate["source_refs"]
    assert "Product default can use customer field validation by default" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l24_customer_feedback_update_boundary(
    tmp_path,
):
    inputs = _build_l16_gate_inputs()
    hindcast = build_r12_independent_hindcast_revalidation(
        artifact_id="r12-independent-hindcast-revalidation-test",
        run_id="r12-l16-test",
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
    )
    trial = build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
        artifact_id=(
            "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-test"
        ),
        run_id="r12-l17-test",
        r12_independent_hindcast_revalidation=hindcast,
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        prediction_lock_timestamp="2026-06-27T14:45:00Z",
    )
    ingestion = build_r12_pre_outcome_or_customer_field_outcome_ingestion(
        artifact_id="r12-pre-outcome-or-customer-field-outcome-ingestion-test",
        run_id="r12-l18-test",
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        availability_checked_at="2026-06-27T14:55:00Z",
    )
    revalidation = (
        build_r12_pre_outcome_or_customer_field_outcome_revalidation(
            artifact_id=(
                "r12-pre-outcome-or-customer-field-outcome-revalidation-test"
            ),
            run_id="r12-l19-test",
            r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
            revalidation_requested_at="2026-06-27T15:05:00Z",
        )
    )
    arrival = build_r12_target_outcome_or_customer_field_slice_arrival(
        artifact_id="r12-target-outcome-or-customer-field-slice-arrival-test",
        run_id="r12-l20-test",
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        arrival_checked_at="2026-06-27T15:30:00Z",
    )
    handoff = build_r12_customer_field_slice_handoff_package(
        artifact_id="r12-customer-field-slice-handoff-package-test",
        run_id="r12-l21-test",
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        generated_at="2026-06-27T15:45:00Z",
        template_output_path=(
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
    )
    customer_slice = tmp_path / "customer-field-slice.csv"
    _write_valid_customer_slice(customer_slice)
    intake = build_r12_customer_field_slice_intake_validation(
        artifact_id="r12-customer-field-slice-intake-validation-test",
        run_id="r12-l22-test",
        r12_customer_field_slice_handoff_package=handoff,
        intake_checked_at="2026-06-28T09:00:00Z",
        customer_field_slice_path=customer_slice,
    )
    customer_revalidation = build_r12_customer_field_slice_revalidation(
        artifact_id="r12-customer-field-slice-revalidation-test",
        run_id="r12-l23-test",
        r12_customer_field_slice_intake_validation=intake,
        revalidation_checked_at="2026-06-28T09:15:00Z",
    )
    feedback = build_r12_customer_field_outcome_feedback_update(
        artifact_id="r12-customer-field-outcome-feedback-update-test",
        run_id="r12-l24-test",
        r12_customer_field_slice_revalidation=customer_revalidation,
        feedback_generated_at="2026-06-28T10:00:00Z",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l24-product-test",
        r12_transfer_validation=inputs["transfer"],
        r12_high_risk_holdout_registry=inputs["registry"],
        r12_high_risk_holdout_transfer_replay=inputs["replay"],
        r12_recall_oriented_update=inputs["recall_update"],
        r12_recall_update_false_alarm_stress_test=inputs["stress"],
        r12_recall_false_alarm_mitigation_candidate=inputs["mitigation"],
        r12_recall_mitigation_holdout_validation=inputs["holdout_validation"],
        r12_recall_mitigation_independent_holdout_data=inputs["independent_data"],
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            inputs["external_or_customer_contract"]
        ),
        r12_external_or_customer_holdout_raw_slice=inputs["raw_slice"],
        r12_recall_mitigation_external_holdout_revalidation=(
            inputs["revalidation"]
        ),
        r12_pre_outcome_or_independent_prediction_packet=inputs["packet"],
        r12_independent_hindcast_revalidation=hindcast,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=trial,
        r12_pre_outcome_or_customer_field_outcome_ingestion=ingestion,
        r12_pre_outcome_or_customer_field_outcome_revalidation=revalidation,
        r12_target_outcome_or_customer_field_slice_arrival=arrival,
        r12_customer_field_slice_handoff_package=handoff,
        r12_customer_field_slice_intake_validation=intake,
        r12_customer_field_slice_revalidation=customer_revalidation,
        r12_customer_field_outcome_feedback_update=feedback,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_field_outcome_feedback_update_boundary"
    ]
    assert boundary == {
        "feedback_update_status": (
            "r12_customer_field_outcome_feedback_update_candidates_ready_guarded"
        ),
        "acceptance_decision": (
            "accept_customer_feedback_update_candidates_for_shadow_review"
        ),
        "metrics_consumed": True,
        "field_outcome_validated": True,
        "candidate_count": 2,
        "prompt_or_persona_manual_patch_allowed": False,
        "product_default_allowed": False,
        "next_required_artifact": "r12_customer_feedback_update_shadow_replay",
    }
    assert gate["acceptance_gates"][
        "r12_customer_field_feedback_update_candidate_count"
    ] == 2
    assert gate["acceptance_gates"][
        "r12_customer_field_feedback_update_metrics_consumed"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_field_feedback_update_product_default_allowed"
    ] is False
    assert "r12-customer-field-outcome-feedback-update-test" in gate["source_refs"]
    assert "Product default can use customer feedback update by default" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l25_customer_feedback_shadow_replay_boundary():
    shadow_replay = build_r12_customer_feedback_update_shadow_replay(
        artifact_id="r12-customer-feedback-update-shadow-replay-test",
        run_id="r12-l25-test",
        r12_customer_field_outcome_feedback_update=_load_current_l24(),
        replay_requested_at="2026-06-28T10:30:00Z",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l25-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_feedback_update_shadow_replay=shadow_replay,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_feedback_update_shadow_replay_boundary"
    ]
    assert boundary == {
        "shadow_replay_status": (
            "r12_customer_feedback_update_shadow_replay_blocked_no_candidates"
        ),
        "acceptance_decision": "reject_shadow_replay_no_feedback_candidates",
        "candidate_count": 0,
        "replay_executed": False,
        "accepted_candidate_count": 0,
        "at_least_one_candidate_passed": False,
        "product_default_allowed": False,
        "next_required_artifact": "validated_customer_field_feedback_update",
    }
    assert gate["acceptance_gates"][
        "r12_customer_feedback_shadow_replay_executed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_feedback_shadow_replay_accepted_candidate_count"
    ] == 0
    assert gate["acceptance_gates"][
        "r12_customer_feedback_shadow_replay_product_default_allowed"
    ] is False
    assert "r12-customer-feedback-update-shadow-replay-test" in gate[
        "source_refs"
    ]
    assert "Product default can use customer feedback shadow replay by default" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l26_customer_feedback_holdout_review_boundary():
    holdout_review = build_r12_customer_feedback_shadow_replay_holdout_review(
        artifact_id="r12-customer-feedback-shadow-replay-holdout-review-test",
        run_id="r12-l26-test",
        r12_customer_feedback_update_shadow_replay=_load_current_l25(),
        holdout_review_requested_at="2026-06-28T11:00:00Z",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l26-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_feedback_shadow_replay_holdout_review=holdout_review,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_feedback_shadow_replay_holdout_review_boundary"
    ]
    assert boundary == {
        "holdout_review_status": (
            "r12_customer_feedback_shadow_replay_holdout_review_blocked_no_shadow_candidates"
        ),
        "acceptance_decision": "reject_holdout_review_no_shadow_candidates",
        "accepted_shadow_candidate_count": 0,
        "independent_holdout_case_count": 0,
        "holdout_review_executed": False,
        "holdout_review_passed": False,
        "product_default_allowed": False,
        "next_required_artifact": "customer_feedback_shadow_replay_holdout_review",
    }
    assert gate["acceptance_gates"][
        "r12_customer_feedback_holdout_review_executed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_feedback_holdout_review_passed"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_feedback_holdout_review_product_default_allowed"
    ] is False
    assert "r12-customer-feedback-shadow-replay-holdout-review-test" in gate[
        "source_refs"
    ]
    assert "Product default can use customer feedback holdout review by default" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l27_customer_validation_workflow_boundary():
    workflow = build_r12_customer_validation_workflow_status(
        artifact_id="r12-customer-validation-workflow-status-test",
        run_id="r12-l27-test",
        workflow_generated_at="2026-06-28T12:00:00Z",
        r12_target_outcome_or_customer_field_slice_arrival=_load_current_l20(),
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_field_slice_intake_validation=_load_current_l22(),
        r12_customer_field_slice_revalidation=_load_current_l23(),
        r12_customer_field_outcome_feedback_update=_load_current_l24(),
        r12_customer_feedback_update_shadow_replay=_load_current_l25(),
        r12_customer_feedback_shadow_replay_holdout_review=_load_current_l26(),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l27-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_validation_workflow_status=workflow,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_validation_workflow_status_boundary"
    ]
    assert boundary == {
        "workflow_status": "r12_customer_validation_workflow_waiting_for_source",
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "blocking_artifact_id": (
            "r12-target-outcome-or-customer-field-slice-arrival-current-001"
        ),
        "source_arrived": False,
        "field_outcome_validated": False,
        "feedback_candidate_count": 0,
        "shadow_replay_executed": False,
        "holdout_review_executed": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "customer_field_slice_submission_or_target_outcome_artifact"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_validation_workflow_status_package_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_validation_workflow_field_outcome_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_validation_workflow_product_default_allowed"
    ] is False
    assert "r12-customer-validation-workflow-status-test" in gate["source_refs"]
    assert "field validation 已完成" in gate["blocked_claims"]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l28_customer_trial_readiness_boundary():
    trial_package = build_r12_customer_trial_readiness_package(
        artifact_id="r12-customer-trial-readiness-package-test",
        run_id="r12-l28-test",
        package_generated_at="2026-06-28T12:30:00Z",
        r12_customer_field_slice_handoff_package=_load_current_l21(),
        r12_customer_validation_workflow_status=_load_current_l27(),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l28-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_trial_readiness_package=trial_package,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_readiness_package_boundary"
    ]
    assert boundary == {
        "trial_package_status": (
            "r12_customer_trial_readiness_package_ready_guarded_source_pending"
        ),
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "customer_data_request_ready": True,
        "template_output_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
        "minimum_case_count": 10,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "customer_field_slice_submission_or_target_outcome_artifact"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_trial_readiness_package_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_trial_readiness_field_outcome_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_trial_readiness_product_default_allowed"
    ] is False
    assert "r12-customer-trial-readiness-package-test" in gate["source_refs"]
    assert "customer trial has produced accepted feedback update" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l29_customer_trial_operational_boundary():
    operational_check = build_r12_customer_trial_operational_check(
        artifact_id="r12-customer-trial-operational-check-test",
        run_id="r12-l29-test",
        checked_at="2026-06-28T13:20:00Z",
        r12_customer_trial_readiness_package=_load_current_l28(),
        repo_root=Path(__file__).resolve().parents[1],
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l29-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_trial_operational_check=operational_check,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_operational_check_boundary"
    ]
    assert boundary == {
        "operational_check_status": (
            "r12_customer_trial_operational_check_ready_source_pending"
        ),
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "customer_trial_request_operationally_ready": True,
        "template_path_resolvable": True,
        "template_required_fields_present": True,
        "source_registry_resolvable": True,
        "operator_runbook_declared": True,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "customer_field_slice_submission_or_target_outcome_artifact"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_trial_operational_check_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_trial_operationally_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_trial_operational_field_outcome_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_trial_operational_product_default_allowed"
    ] is False
    assert "r12-customer-trial-operational-check-test" in gate["source_refs"]
    assert "customer trial produced accepted feedback update" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l30_customer_trial_launch_boundary():
    launch_package = build_r12_customer_trial_launch_handoff_package(
        artifact_id="r12-customer-trial-launch-handoff-package-test",
        run_id="r12-l30-test",
        generated_at="2026-06-28T13:50:00Z",
        r12_customer_trial_readiness_package=_load_current_l28(),
        r12_customer_trial_operational_check=_load_current_l29(),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l30-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_trial_launch_handoff_package=launch_package,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_launch_handoff_package_boundary"
    ]
    assert boundary == {
        "launch_package_status": (
            "r12_customer_trial_launch_handoff_package_ready_source_pending"
        ),
        "current_stage": "source_arrival_pending",
        "next_action": "collect_customer_field_slice_or_wait_for_target_outcome",
        "launch_handoff_ready": True,
        "template_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
        "minimum_case_count": 10,
        "required_field_count": 7,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "customer_field_slice_submission_or_target_outcome_artifact"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_handoff_package_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_handoff_field_outcome_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_handoff_product_default_allowed"
    ] is False
    assert "r12-customer-trial-launch-handoff-package-test" in gate["source_refs"]
    assert "customer trial produced accepted feedback update" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l31_customer_trial_packet_export_boundary(
    tmp_path,
):
    packet_export = build_r12_customer_trial_launch_packet_export(
        artifact_id="r12-customer-trial-launch-packet-export-test",
        run_id="r12-l31-test",
        exported_at="2026-06-28T14:20:00Z",
        r12_customer_trial_launch_handoff_package=_load_current_l30(),
        markdown_output_path=tmp_path / "packet.md",
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l31-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_trial_launch_packet_export=packet_export,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_launch_packet_export_boundary"
    ]
    assert boundary == {
        "packet_export_status": (
            "r12_customer_trial_launch_packet_export_ready_source_pending"
        ),
        "current_stage": "source_arrival_pending",
        "launch_handoff_ready": True,
        "markdown_export_written": True,
        "markdown_output_path": str(tmp_path / "packet.md"),
        "customer_field_slice_present": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "customer_field_slice_submission_or_target_outcome_artifact"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_packet_export_ready"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_packet_field_outcome_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_packet_product_default_allowed"
    ] is False
    assert "r12-customer-trial-launch-packet-export-test" in gate["source_refs"]
    assert "customer trial produced accepted feedback update" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_surfaces_l32_customer_trial_bundle_boundary():
    bundle_verification = build_r12_customer_trial_launch_bundle_verification(
        artifact_id="r12-customer-trial-launch-bundle-verification-test",
        run_id="r12-l32-test",
        verified_at="2026-06-28T15:10:00Z",
        r12_customer_trial_launch_packet_export=_load_current_l31(),
        r12_customer_trial_launch_packet_export_path=_current_l31_path(),
        repo_root=_repo_root(),
    )

    gate = build_r12_product_support_gate(
        artifact_id="r12-product-support-gate-test",
        run_id="r12-l32-product-test",
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_customer_trial_launch_bundle_verification=bundle_verification,
    )

    boundary = gate["transfer_evidence_card"]["evidence_summary"][
        "customer_trial_launch_bundle_verification_boundary"
    ]
    assert boundary == {
        "bundle_verification_status": (
            "r12_customer_trial_launch_bundle_verification_ready_source_pending"
        ),
        "current_stage": "source_arrival_pending",
        "launch_bundle_verified": True,
        "required_item_count": 4,
        "resolved_required_item_count": 4,
        "missing_required_item_ids": [],
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "next_required_artifact": (
            "customer_field_slice_submission_or_target_outcome_artifact"
        ),
    }
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_bundle_verified"
    ] is True
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_bundle_field_outcome_validated"
    ] is False
    assert gate["acceptance_gates"][
        "r12_customer_trial_launch_bundle_product_default_allowed"
    ] is False
    assert "r12-customer-trial-launch-bundle-verification-test" in gate[
        "source_refs"
    ]
    assert "customer trial produced accepted feedback update" in gate[
        "blocked_claims"
    ]
    json.dumps(gate, allow_nan=False)


def test_r12_product_support_gate_cli_writes_artifact(tmp_path):
    transfer_path = tmp_path / "r12-transfer-validation.json"
    output = tmp_path / "r12-product-support-gate.json"
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_product_support_gate.py",
            "--artifact-id",
            "r12-product-support-gate-cli",
            "--run-id",
            "r12-l4-test",
            "--r12-transfer-validation-path",
            str(transfer_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-product-support-gate-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-product-support-gate-cli",
        "output": str(output),
        "status": "r12_product_support_gate_ready_guarded",
    }


def _build_l16_gate_inputs():
    transfer = _load_current_transfer_validation()
    registry = build_r12_high_risk_holdout_registry(
        artifact_id="r12-high-risk-holdout-registry-test",
        run_id="r12-l5-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
    )
    replay = build_r12_high_risk_holdout_transfer_replay(
        artifact_id="r12-high-risk-holdout-transfer-replay-test",
        run_id="r12-l6-test",
        r12_high_risk_holdout_registry=registry,
        r12_transfer_validation=transfer,
    )
    recall_update = build_r12_recall_oriented_update(
        artifact_id="r12-recall-oriented-update-test",
        run_id="r12-l7-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_high_risk_holdout_transfer_replay=replay,
    )
    stress = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
    )
    mitigation = build_r12_recall_false_alarm_mitigation_candidate(
        artifact_id="r12-recall-false-alarm-mitigation-candidate-test",
        run_id="r12-l9-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_update_false_alarm_stress_test=stress,
    )
    holdout_validation = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_oriented_update=recall_update,
        r12_recall_false_alarm_mitigation_candidate=mitigation,
    )
    independent_data = build_r12_recall_mitigation_independent_holdout_data(
        artifact_id="r12-recall-mitigation-independent-holdout-data-test",
        run_id="r12-l11-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=transfer,
        r12_recall_mitigation_holdout_validation=holdout_validation,
        r10_external_evidence_registry=_load_current_external_registry(),
    )
    external_or_customer_contract = (
        build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            artifact_id=(
                "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
            ),
            run_id="r12-l12-test",
            r12_recall_mitigation_independent_holdout_data=independent_data,
            r10_external_evidence_registry=_load_current_external_registry(),
        )
    )
    raw_slice = build_r12_external_or_customer_holdout_raw_slice(
        artifact_id="r12-external-or-customer-holdout-raw-slice-test",
        run_id="r12-l13-test",
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            external_or_customer_contract
        ),
    )
    revalidation = build_r12_recall_mitigation_external_holdout_revalidation(
        artifact_id="r12-recall-mitigation-external-holdout-revalidation-test",
        run_id="r12-l14-test",
        r12_external_or_customer_holdout_raw_slice=raw_slice,
    )
    packet = build_r12_pre_outcome_or_independent_prediction_packet(
        artifact_id="r12-pre-outcome-or-independent-prediction-packet-test",
        run_id="r12-l15-test",
        r12_recall_mitigation_external_holdout_revalidation=revalidation,
        r12_external_or_customer_holdout_raw_slice=raw_slice,
    )
    return {
        "transfer": transfer,
        "registry": registry,
        "replay": replay,
        "recall_update": recall_update,
        "stress": stress,
        "mitigation": mitigation,
        "holdout_validation": holdout_validation,
        "independent_data": independent_data,
        "external_or_customer_contract": external_or_customer_contract,
        "raw_slice": raw_slice,
        "revalidation": revalidation,
        "packet": packet,
    }


def _load_current_transfer_validation():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_transfer_validation/"
            "r12-transfer-validation-current-001.json"
        ).read_text()
    )


def _load_current_hps_ingestion():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r10_hps_policy_reaction_ingestion/"
            "r10-hps-policy-reaction-ingestion-current-001.json"
        ).read_text()
    )


def _load_current_external_registry():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r10_external_evidence_registry/"
            "r10-external-evidence-registry-current-001.json"
        ).read_text()
    )


def _load_current_l20():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_target_outcome_or_customer_field_slice_arrival/"
            "r12-target-outcome-or-customer-field-slice-arrival-current-001.json"
        ).read_text()
    )


def _load_current_l21():
    return json.loads(_current_l21_path().read_text())


def _current_l21_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/"
        "r12_customer_field_slice_handoff_package/"
        "r12-customer-field-slice-handoff-package-current-001.json"
    )


def _load_current_l22():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_field_slice_intake_validation/"
            "r12-customer-field-slice-intake-validation-current-001.json"
        ).read_text()
    )


def _load_current_l23():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_field_slice_revalidation/"
            "r12-customer-field-slice-revalidation-current-001.json"
        ).read_text()
    )


def _load_current_l24():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_field_outcome_feedback_update/"
            "r12-customer-field-outcome-feedback-update-current-001.json"
        ).read_text()
    )


def _load_current_l25():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_feedback_update_shadow_replay/"
            "r12-customer-feedback-update-shadow-replay-current-001.json"
        ).read_text()
    )


def _load_current_l26():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_feedback_shadow_replay_holdout_review/"
            "r12-customer-feedback-shadow-replay-holdout-review-current-001.json"
        ).read_text()
    )


def _load_current_l27():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_validation_workflow_status/"
            "r12-customer-validation-workflow-status-current-001.json"
        ).read_text()
    )


def _load_current_l28():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_trial_readiness_package/"
            "r12-customer-trial-readiness-package-current-001.json"
        ).read_text()
    )


def _load_current_l29():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_trial_operational_check/"
            "r12-customer-trial-operational-check-current-001.json"
        ).read_text()
    )


def _load_current_l30():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_customer_trial_launch_handoff_package/"
            "r12-customer-trial-launch-handoff-package-current-001.json"
        ).read_text()
    )


def _load_current_l31():
    return json.loads(_current_l31_path().read_text())


def _current_l31_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/"
        "r12_customer_trial_launch_packet_export/"
        "r12-customer-trial-launch-packet-export-current-001.json"
    )


def _load_current_l32():
    return json.loads(_current_l32_path().read_text())


def _current_l32_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/"
        "r12_customer_trial_launch_bundle_verification/"
        "r12-customer-trial-launch-bundle-verification-current-001.json"
    )


def _load_current_l34():
    return json.loads(_current_l34_path().read_text())


def _current_l34_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/"
        "r12_customer_field_slice_operator_rehearsal/"
        "r12-customer-field-slice-operator-rehearsal-current-001.json"
    )


def _load_current_l35():
    return json.loads(_current_l35_path().read_text())


def _current_l35_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/"
        "r12_customer_feedback_loop_operator_rehearsal/"
        "r12-customer-feedback-loop-operator-rehearsal-current-001.json"
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_valid_customer_slice(path: Path) -> None:
    fields = [
        "case_id",
        "segment_id",
        "scenario_id",
        "prediction_share_or_score",
        "observed_outcome",
        "outcome_timestamp",
        "customer_approval_reference",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for idx in range(10):
            writer.writerow(
                {
                    "case_id": f"case-{idx}",
                    "segment_id": f"segment-{idx % 3}",
                    "scenario_id": "scenario-001",
                    "prediction_share_or_score": f"{0.10 + idx * 0.03:.3f}",
                    "observed_outcome": f"{0.12 + idx * 0.03:.3f}",
                    "outcome_timestamp": "2026-07-15T00:00:00Z",
                    "customer_approval_reference": "approval-2026-06-27",
                }
            )
