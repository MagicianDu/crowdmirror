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
