from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)
from experiments.r12_high_risk_holdout_registry import (
    R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION,
)
from experiments.r12_high_risk_holdout_transfer_replay import (
    R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION,
)
from experiments.r12_recall_oriented_update import (
    R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION,
)
from experiments.r12_recall_update_false_alarm_stress_test import (
    R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION,
)
from experiments.r12_recall_false_alarm_mitigation_candidate import (
    R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_holdout_validation import (
    R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_independent_holdout_data import (
    R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_external_holdout_ingestion_or_customer_slice import (
    R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION,
)
from experiments.r12_external_or_customer_holdout_raw_slice import (
    R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_external_holdout_revalidation import (
    R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION,
)
from experiments.r12_pre_outcome_or_independent_prediction_packet import (
    R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION,
)
from experiments.r12_independent_hindcast_revalidation import (
    R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION,
)
from experiments.r12_pre_outcome_prediction_trial_or_customer_field_revalidation import (
    R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION,
)
from experiments.r12_pre_outcome_or_customer_field_outcome_ingestion import (
    R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION,
)
from experiments.r12_pre_outcome_or_customer_field_outcome_revalidation import (
    R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION,
)
from experiments.r12_target_outcome_or_customer_field_slice_arrival import (
    R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_handoff_package import (
    R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_intake_validation import (
    R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_revalidation import (
    R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION,
)
from experiments.r12_customer_field_outcome_feedback_update import (
    R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION,
)
from experiments.r12_customer_feedback_update_shadow_replay import (
    R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION,
)
from experiments.r12_customer_feedback_shadow_replay_holdout_review import (
    R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION,
)
from experiments.r12_customer_validation_workflow_status import (
    R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_readiness_package import (
    R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_operational_check import (
    R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_launch_handoff_package import (
    R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_launch_packet_export import (
    R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_launch_bundle_verification import (
    R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION,
)
from experiments.r12_customer_field_slice_operator_rehearsal import (
    R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION,
)
from experiments.r12_customer_feedback_loop_operator_rehearsal import (
    R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION,
)
from experiments.r12_customer_trial_evidence_ledger import (
    R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION,
)


R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION = "r12-product-support-gate-v1"
R12_PRODUCT_SUPPORT_GATE_CLAIM_BOUNDARY = (
    "R12 Product support gate artifact. It allows Product to display a "
    "source-backed R12 transfer-validation evidence card as secondary evidence, "
    "while preserving guarded baseline primary decisions. It is not Product "
    "core method validation, not field validation, and not runtime default "
    "authorization."
)


def build_r12_product_support_gate(
    *,
    artifact_id: str,
    run_id: str,
    r12_transfer_validation: dict[str, Any],
    r12_high_risk_holdout_registry: dict[str, Any] | None = None,
    r12_high_risk_holdout_transfer_replay: dict[str, Any] | None = None,
    r12_recall_oriented_update: dict[str, Any] | None = None,
    r12_recall_update_false_alarm_stress_test: dict[str, Any] | None = None,
    r12_recall_false_alarm_mitigation_candidate: dict[str, Any] | None = None,
    r12_recall_mitigation_holdout_validation: dict[str, Any] | None = None,
    r12_recall_mitigation_independent_holdout_data: dict[str, Any] | None = None,
    r12_recall_mitigation_external_holdout_ingestion_or_customer_slice: dict[
        str, Any
    ]
    | None = None,
    r12_external_or_customer_holdout_raw_slice: dict[str, Any] | None = None,
    r12_recall_mitigation_external_holdout_revalidation: dict[
        str, Any
    ]
    | None = None,
    r12_pre_outcome_or_independent_prediction_packet: dict[
        str, Any
    ]
    | None = None,
    r12_independent_hindcast_revalidation: dict[str, Any] | None = None,
    r12_pre_outcome_prediction_trial_or_customer_field_revalidation: dict[
        str, Any
    ]
    | None = None,
    r12_pre_outcome_or_customer_field_outcome_ingestion: dict[
        str, Any
    ]
    | None = None,
    r12_pre_outcome_or_customer_field_outcome_revalidation: dict[
        str, Any
    ]
    | None = None,
    r12_target_outcome_or_customer_field_slice_arrival: dict[
        str, Any
    ]
    | None = None,
    r12_customer_field_slice_handoff_package: dict[str, Any] | None = None,
    r12_customer_field_slice_intake_validation: dict[str, Any] | None = None,
    r12_customer_field_slice_revalidation: dict[str, Any] | None = None,
    r12_customer_field_outcome_feedback_update: dict[str, Any] | None = None,
    r12_customer_feedback_update_shadow_replay: dict[str, Any] | None = None,
    r12_customer_feedback_shadow_replay_holdout_review: (
        dict[str, Any] | None
    ) = None,
    r12_customer_validation_workflow_status: dict[str, Any] | None = None,
    r12_customer_trial_readiness_package: dict[str, Any] | None = None,
    r12_customer_trial_operational_check: dict[str, Any] | None = None,
    r12_customer_trial_launch_handoff_package: dict[str, Any] | None = None,
    r12_customer_trial_launch_packet_export: dict[str, Any] | None = None,
    r12_customer_trial_launch_bundle_verification: dict[str, Any] | None = None,
    r12_customer_field_slice_operator_rehearsal: dict[str, Any] | None = None,
    r12_customer_feedback_loop_operator_rehearsal: dict[
        str, Any
    ] | None = None,
    r12_customer_trial_evidence_ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_transfer_validation(r12_transfer_validation)
    if r12_high_risk_holdout_registry is not None:
        _validate_high_risk_registry(r12_high_risk_holdout_registry)
    if r12_high_risk_holdout_transfer_replay is not None:
        _validate_high_risk_replay(r12_high_risk_holdout_transfer_replay)
    if r12_recall_oriented_update is not None:
        _validate_recall_oriented_update(r12_recall_oriented_update)
    if r12_recall_update_false_alarm_stress_test is not None:
        _validate_recall_false_alarm_stress(
            r12_recall_update_false_alarm_stress_test
        )
    if r12_recall_false_alarm_mitigation_candidate is not None:
        _validate_recall_false_alarm_mitigation(
            r12_recall_false_alarm_mitigation_candidate
        )
    if r12_recall_mitigation_holdout_validation is not None:
        _validate_recall_mitigation_holdout_validation(
            r12_recall_mitigation_holdout_validation
        )
    if r12_recall_mitigation_independent_holdout_data is not None:
        _validate_recall_mitigation_independent_holdout_data(
            r12_recall_mitigation_independent_holdout_data
        )
    if (
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
        is not None
    ):
        _validate_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
        )
    if r12_external_or_customer_holdout_raw_slice is not None:
        _validate_external_or_customer_holdout_raw_slice(
            r12_external_or_customer_holdout_raw_slice
        )
    if r12_recall_mitigation_external_holdout_revalidation is not None:
        _validate_recall_mitigation_external_holdout_revalidation(
            r12_recall_mitigation_external_holdout_revalidation
        )
    if r12_pre_outcome_or_independent_prediction_packet is not None:
        _validate_pre_outcome_or_independent_prediction_packet(
            r12_pre_outcome_or_independent_prediction_packet
        )
    if r12_independent_hindcast_revalidation is not None:
        _validate_independent_hindcast_revalidation(
            r12_independent_hindcast_revalidation
        )
    if (
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation
        is not None
    ):
        _validate_pre_outcome_prediction_trial_or_customer_field_revalidation(
            r12_pre_outcome_prediction_trial_or_customer_field_revalidation
        )
    if r12_pre_outcome_or_customer_field_outcome_ingestion is not None:
        _validate_pre_outcome_or_customer_field_outcome_ingestion(
            r12_pre_outcome_or_customer_field_outcome_ingestion
        )
    if r12_pre_outcome_or_customer_field_outcome_revalidation is not None:
        _validate_pre_outcome_or_customer_field_outcome_revalidation(
            r12_pre_outcome_or_customer_field_outcome_revalidation
        )
    if r12_target_outcome_or_customer_field_slice_arrival is not None:
        _validate_target_outcome_or_customer_field_slice_arrival(
            r12_target_outcome_or_customer_field_slice_arrival
        )
    if r12_customer_field_slice_handoff_package is not None:
        _validate_customer_field_slice_handoff_package(
            r12_customer_field_slice_handoff_package
        )
    if r12_customer_field_slice_intake_validation is not None:
        _validate_customer_field_slice_intake_validation(
            r12_customer_field_slice_intake_validation
        )
    if r12_customer_field_slice_revalidation is not None:
        _validate_customer_field_slice_revalidation(
            r12_customer_field_slice_revalidation
        )
    if r12_customer_field_outcome_feedback_update is not None:
        _validate_customer_field_outcome_feedback_update(
            r12_customer_field_outcome_feedback_update
        )
    if r12_customer_feedback_update_shadow_replay is not None:
        _validate_customer_feedback_update_shadow_replay(
            r12_customer_feedback_update_shadow_replay
        )
    if r12_customer_feedback_shadow_replay_holdout_review is not None:
        _validate_customer_feedback_shadow_replay_holdout_review(
            r12_customer_feedback_shadow_replay_holdout_review
        )
    if r12_customer_validation_workflow_status is not None:
        _validate_customer_validation_workflow_status(
            r12_customer_validation_workflow_status
        )
    if r12_customer_trial_readiness_package is not None:
        _validate_customer_trial_readiness_package(
            r12_customer_trial_readiness_package
        )
    if r12_customer_trial_operational_check is not None:
        _validate_customer_trial_operational_check(
            r12_customer_trial_operational_check
        )
    if r12_customer_trial_launch_handoff_package is not None:
        _validate_customer_trial_launch_handoff_package(
            r12_customer_trial_launch_handoff_package
        )
    if r12_customer_trial_launch_packet_export is not None:
        _validate_customer_trial_launch_packet_export(
            r12_customer_trial_launch_packet_export
        )
    if r12_customer_trial_launch_bundle_verification is not None:
        _validate_customer_trial_launch_bundle_verification(
            r12_customer_trial_launch_bundle_verification
        )
    if r12_customer_field_slice_operator_rehearsal is not None:
        _validate_customer_field_slice_operator_rehearsal(
            r12_customer_field_slice_operator_rehearsal
        )
    if r12_customer_feedback_loop_operator_rehearsal is not None:
        _validate_customer_feedback_loop_operator_rehearsal(
            r12_customer_feedback_loop_operator_rehearsal
        )
    if r12_customer_trial_evidence_ledger is not None:
        _validate_customer_trial_evidence_ledger(
            r12_customer_trial_evidence_ledger
        )
    positive_transfer = (
        r12_transfer_validation["acceptance_gates"]["positive_transfer_guarded"]
        is True
    )
    high_risk_boundary = _high_risk_holdout_boundary(
        r12_high_risk_holdout_registry
    )
    high_risk_replay_boundary = _high_risk_replay_boundary(
        r12_high_risk_holdout_transfer_replay
    )
    recall_update_boundary = _recall_oriented_update_boundary(
        r12_recall_oriented_update
    )
    recall_false_alarm_stress_boundary = _recall_false_alarm_stress_boundary(
        r12_recall_update_false_alarm_stress_test
    )
    recall_false_alarm_mitigation_boundary = (
        _recall_false_alarm_mitigation_boundary(
            r12_recall_false_alarm_mitigation_candidate
        )
    )
    recall_mitigation_holdout_validation_boundary = (
        _recall_mitigation_holdout_validation_boundary(
            r12_recall_mitigation_holdout_validation
        )
    )
    recall_mitigation_independent_holdout_data_boundary = (
        _recall_mitigation_independent_holdout_data_boundary(
            r12_recall_mitigation_independent_holdout_data
        )
    )
    recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary = (
        _recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary(
            r12_recall_mitigation_external_holdout_ingestion_or_customer_slice,
            r12_external_or_customer_holdout_raw_slice=(
                r12_external_or_customer_holdout_raw_slice
            ),
        )
    )
    external_or_customer_holdout_raw_slice_boundary = (
        _external_or_customer_holdout_raw_slice_boundary(
            r12_external_or_customer_holdout_raw_slice
        )
    )
    recall_mitigation_external_holdout_revalidation_boundary = (
        _recall_mitigation_external_holdout_revalidation_boundary(
            r12_recall_mitigation_external_holdout_revalidation
        )
    )
    pre_outcome_or_independent_prediction_packet_boundary = (
        _pre_outcome_or_independent_prediction_packet_boundary(
            r12_pre_outcome_or_independent_prediction_packet
        )
    )
    independent_hindcast_revalidation_boundary = (
        _independent_hindcast_revalidation_boundary(
            r12_independent_hindcast_revalidation
        )
    )
    pre_outcome_prediction_trial_or_customer_field_revalidation_boundary = (
        _pre_outcome_prediction_trial_or_customer_field_revalidation_boundary(
            r12_pre_outcome_prediction_trial_or_customer_field_revalidation
        )
    )
    pre_outcome_or_customer_field_outcome_ingestion_boundary = (
        _pre_outcome_or_customer_field_outcome_ingestion_boundary(
            r12_pre_outcome_or_customer_field_outcome_ingestion
        )
    )
    pre_outcome_or_customer_field_outcome_revalidation_boundary = (
        _pre_outcome_or_customer_field_outcome_revalidation_boundary(
            r12_pre_outcome_or_customer_field_outcome_revalidation
        )
    )
    target_outcome_or_customer_field_slice_arrival_boundary = (
        _target_outcome_or_customer_field_slice_arrival_boundary(
            r12_target_outcome_or_customer_field_slice_arrival
        )
    )
    customer_field_slice_handoff_package_boundary = (
        _customer_field_slice_handoff_package_boundary(
            r12_customer_field_slice_handoff_package
        )
    )
    customer_field_slice_intake_validation_boundary = (
        _customer_field_slice_intake_validation_boundary(
            r12_customer_field_slice_intake_validation
        )
    )
    customer_field_slice_revalidation_boundary = (
        _customer_field_slice_revalidation_boundary(
            r12_customer_field_slice_revalidation
        )
    )
    customer_field_outcome_feedback_update_boundary = (
        _customer_field_outcome_feedback_update_boundary(
            r12_customer_field_outcome_feedback_update
        )
    )
    customer_feedback_update_shadow_replay_boundary = (
        _customer_feedback_update_shadow_replay_boundary(
            r12_customer_feedback_update_shadow_replay
        )
    )
    customer_feedback_shadow_replay_holdout_review_boundary = (
        _customer_feedback_shadow_replay_holdout_review_boundary(
            r12_customer_feedback_shadow_replay_holdout_review
        )
    )
    customer_validation_workflow_status_boundary = (
        _customer_validation_workflow_status_boundary(
            r12_customer_validation_workflow_status
        )
    )
    customer_trial_readiness_package_boundary = (
        _customer_trial_readiness_package_boundary(
            r12_customer_trial_readiness_package
        )
    )
    customer_trial_operational_check_boundary = (
        _customer_trial_operational_check_boundary(
            r12_customer_trial_operational_check
        )
    )
    customer_trial_launch_handoff_package_boundary = (
        _customer_trial_launch_handoff_package_boundary(
            r12_customer_trial_launch_handoff_package
        )
    )
    customer_trial_launch_packet_export_boundary = (
        _customer_trial_launch_packet_export_boundary(
            r12_customer_trial_launch_packet_export
        )
    )
    customer_trial_launch_bundle_verification_boundary = (
        _customer_trial_launch_bundle_verification_boundary(
            r12_customer_trial_launch_bundle_verification
        )
    )
    customer_field_slice_operator_rehearsal_boundary = (
        _customer_field_slice_operator_rehearsal_boundary(
            r12_customer_field_slice_operator_rehearsal
        )
    )
    customer_feedback_loop_operator_rehearsal_boundary = (
        _customer_feedback_loop_operator_rehearsal_boundary(
            r12_customer_feedback_loop_operator_rehearsal
        )
    )
    customer_trial_evidence_ledger_boundary = (
        _customer_trial_evidence_ledger_boundary(
            r12_customer_trial_evidence_ledger
        )
    )
    public_data_validation_scope = _public_data_validation_scope(
        r12_external_or_customer_holdout_raw_slice=(
            r12_external_or_customer_holdout_raw_slice
        ),
        r12_pre_outcome_or_independent_prediction_packet=(
            r12_pre_outcome_or_independent_prediction_packet
        ),
        r12_independent_hindcast_revalidation=(
            r12_independent_hindcast_revalidation
        ),
    )
    public_data_effectiveness_claim_allowed = bool(
        public_data_validation_scope
        and public_data_validation_scope["public_data_effectiveness_claim_allowed"]
    )
    report = {
        "schema_version": R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_product_support_gate_ready_guarded",
        "claim_level": "product_secondary_evidence_only",
        "claim_boundary": R12_PRODUCT_SUPPORT_GATE_CLAIM_BOUNDARY,
        "product_support_contract": {
            "source_backed_only": True,
            "customer_visible_evidence_card_allowed": True,
            "secondary_evidence_card_only": True,
            "customer_visible_primary_claims_use_guarded_baseline": True,
            "r12_can_override_primary_decision": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            **(
                {
                    "public_data_effectiveness_claim_allowed": (
                        public_data_effectiveness_claim_allowed
                    ),
                    "customer_field_validation_required_for_current_stage": False,
                }
                if public_data_validation_scope is not None
                else {}
            ),
        },
        **(
            {"public_data_validation_scope": public_data_validation_scope}
            if public_data_validation_scope is not None
            else {}
        ),
        "transfer_evidence_card": _transfer_evidence_card(
            r12_transfer_validation,
            positive_transfer=positive_transfer,
            high_risk_boundary=high_risk_boundary,
            high_risk_replay_boundary=high_risk_replay_boundary,
            recall_update_boundary=recall_update_boundary,
            recall_false_alarm_stress_boundary=(
                recall_false_alarm_stress_boundary
            ),
            recall_false_alarm_mitigation_boundary=(
                recall_false_alarm_mitigation_boundary
            ),
            recall_mitigation_holdout_validation_boundary=(
                recall_mitigation_holdout_validation_boundary
            ),
            recall_mitigation_independent_holdout_data_boundary=(
                recall_mitigation_independent_holdout_data_boundary
            ),
            recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary=(
                recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary
            ),
            external_or_customer_holdout_raw_slice_boundary=(
                external_or_customer_holdout_raw_slice_boundary
            ),
            recall_mitigation_external_holdout_revalidation_boundary=(
                recall_mitigation_external_holdout_revalidation_boundary
            ),
            pre_outcome_or_independent_prediction_packet_boundary=(
                pre_outcome_or_independent_prediction_packet_boundary
            ),
            independent_hindcast_revalidation_boundary=(
                independent_hindcast_revalidation_boundary
            ),
            pre_outcome_prediction_trial_or_customer_field_revalidation_boundary=(
                pre_outcome_prediction_trial_or_customer_field_revalidation_boundary
            ),
            pre_outcome_or_customer_field_outcome_ingestion_boundary=(
                pre_outcome_or_customer_field_outcome_ingestion_boundary
            ),
            pre_outcome_or_customer_field_outcome_revalidation_boundary=(
                pre_outcome_or_customer_field_outcome_revalidation_boundary
            ),
            target_outcome_or_customer_field_slice_arrival_boundary=(
                target_outcome_or_customer_field_slice_arrival_boundary
            ),
            customer_field_slice_handoff_package_boundary=(
                customer_field_slice_handoff_package_boundary
            ),
            customer_field_slice_intake_validation_boundary=(
                customer_field_slice_intake_validation_boundary
            ),
            customer_field_slice_revalidation_boundary=(
                customer_field_slice_revalidation_boundary
            ),
            customer_field_outcome_feedback_update_boundary=(
                customer_field_outcome_feedback_update_boundary
            ),
            customer_feedback_update_shadow_replay_boundary=(
                customer_feedback_update_shadow_replay_boundary
            ),
            customer_feedback_shadow_replay_holdout_review_boundary=(
                customer_feedback_shadow_replay_holdout_review_boundary
            ),
            customer_validation_workflow_status_boundary=(
                customer_validation_workflow_status_boundary
            ),
            customer_trial_readiness_package_boundary=(
                customer_trial_readiness_package_boundary
            ),
            customer_trial_operational_check_boundary=(
                customer_trial_operational_check_boundary
            ),
            customer_trial_launch_handoff_package_boundary=(
                customer_trial_launch_handoff_package_boundary
            ),
            customer_trial_launch_packet_export_boundary=(
                customer_trial_launch_packet_export_boundary
            ),
            customer_trial_launch_bundle_verification_boundary=(
                customer_trial_launch_bundle_verification_boundary
            ),
            customer_field_slice_operator_rehearsal_boundary=(
                customer_field_slice_operator_rehearsal_boundary
            ),
            customer_feedback_loop_operator_rehearsal_boundary=(
                customer_feedback_loop_operator_rehearsal_boundary
            ),
            customer_trial_evidence_ledger_boundary=(
                customer_trial_evidence_ledger_boundary
            ),
        ),
        "customer_visible_primary_decision": {
            "primary_decision_source": "guarded_baseline_customer_value_report",
            "r12_output_role": "secondary_transfer_evidence_card_only",
            "r12_can_override_primary_decision": False,
            "runtime_default_allowed": False,
        },
        "outcome_review_handoff": {
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
        },
        "acceptance_gates": {
            "r12_transfer_positive_guarded": positive_transfer,
            "customer_visible_evidence_card_allowed": True,
            "secondary_evidence_card_only": True,
            "primary_claims_guarded_baseline_only": True,
            "r12_can_override_primary_decision": False,
            "product_core_method_ready": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            **(
                {
                    "r12_public_data_effectiveness_claim_allowed": (
                        public_data_effectiveness_claim_allowed
                    ),
                    "customer_field_validation_required_for_current_stage": False,
                }
                if public_data_validation_scope is not None
                else {}
            ),
            **(
                {
                    "r12_high_risk_research_holdout_candidates_present": (
                        r12_high_risk_holdout_registry["acceptance_gates"][
                            "high_risk_research_holdout_candidates_present"
                        ]
                    ),
                    "r12_product_default_high_risk_holdout_present": (
                        r12_high_risk_holdout_registry["acceptance_gates"][
                            "product_default_low_sensitive_high_risk_holdout_present"
                        ]
                    ),
                }
                if r12_high_risk_holdout_registry is not None
                else {}
            ),
            **(
                {
                    "r12_high_risk_replay_mae_improved": (
                        r12_high_risk_holdout_transfer_replay["acceptance_gates"][
                            "mae_improved"
                        ]
                    ),
                    "r12_high_risk_replay_recall_improved": (
                        r12_high_risk_holdout_transfer_replay["acceptance_gates"][
                            "static_prior_miss_recovery_improved"
                        ]
                        or r12_high_risk_holdout_transfer_replay["acceptance_gates"][
                            "abnormal_segment_recall_improved"
                        ]
                    ),
                }
                if r12_high_risk_holdout_transfer_replay is not None
                else {}
            ),
            **(
                {
                    "r12_recall_oriented_update_recall_improved": (
                        r12_recall_oriented_update["acceptance_gates"][
                            "recall_improved"
                        ]
                    ),
                    "r12_recall_oriented_update_false_alarm_non_regression": (
                        r12_recall_oriented_update["acceptance_gates"][
                            "false_alarm_non_regression"
                        ]
                    ),
                    "r12_recall_oriented_update_product_default_allowed": (
                        r12_recall_oriented_update["acceptance_gates"][
                            "product_default_allowed"
                        ]
                    ),
                }
                if r12_recall_oriented_update is not None
                else {}
            ),
            **(
                {
                    "r12_recall_false_alarm_stress_passed": (
                        r12_recall_update_false_alarm_stress_test[
                            "acceptance_gates"
                        ]["stress_test_passed"]
                    ),
                    "r12_recall_false_alarm_stress_product_default_allowed": (
                        r12_recall_update_false_alarm_stress_test[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                    "r12_recall_false_alarm_stress_sensitive_concentration": (
                        r12_recall_update_false_alarm_stress_test[
                            "acceptance_gates"
                        ][
                            "new_false_alarms_concentrated_on_sensitive_axis"
                        ]
                    ),
                }
                if r12_recall_update_false_alarm_stress_test is not None
                else {}
            ),
            **(
                {
                    "r12_recall_false_alarm_mitigation_selected": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["mitigation_candidate_selected"]
                    ),
                    "r12_recall_false_alarm_mitigation_false_alarm_non_regression": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["false_alarm_non_regression"]
                    ),
                    "r12_recall_false_alarm_mitigation_product_default_allowed": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                    "r12_recall_false_alarm_mitigation_overfit_risk_present": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["overfit_risk_present"]
                    ),
                }
                if r12_recall_false_alarm_mitigation_candidate is not None
                else {}
            ),
            **(
                {
                    "r12_recall_mitigation_holdout_validated": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["mitigation_holdout_validated"]
                    ),
                    "r12_recall_mitigation_holdout_product_default_allowed": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                    "r12_recall_mitigation_holdout_independent_present": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["independent_holdout_present"]
                    ),
                    "r12_recall_mitigation_holdout_leave_one_stable": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["leave_one_false_alarm_band_stable"]
                    ),
                }
                if r12_recall_mitigation_holdout_validation is not None
                else {}
            ),
            **(
                {
                    "r12_recall_mitigation_independent_data_ready": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["mitigation_independent_data_ready"]
                    ),
                    "r12_recall_mitigation_independent_external_data_ingested": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["external_independent_data_ingested"]
                    ),
                    "r12_recall_mitigation_independent_low_sensitive_recall_evaluable": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["low_sensitive_recall_evaluable"]
                    ),
                    "r12_recall_mitigation_independent_product_default_allowed": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_recall_mitigation_independent_holdout_data is not None
                else {}
            ),
            **(
                {
                    "r12_recall_mitigation_external_or_customer_contract_ready": (
                        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                            "acceptance_gates"
                        ]["ingestion_contract_ready"]
                        and r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                            "acceptance_gates"
                        ]["customer_slice_contract_ready"]
                    ),
                    "r12_recall_mitigation_external_or_customer_raw_slice_present": (
                        (
                            r12_external_or_customer_holdout_raw_slice
                            or r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
                        )["acceptance_gates"][
                            "raw_external_or_customer_slice_present"
                        ]
                    ),
                    "r12_recall_mitigation_external_or_customer_revalidation_ready": (
                        (
                            r12_external_or_customer_holdout_raw_slice[
                                "acceptance_gates"
                            ]["external_holdout_revalidation_ready"]
                            if r12_external_or_customer_holdout_raw_slice
                            is not None
                            else r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                                "acceptance_gates"
                            ][
                                "independent_holdout_revalidation_ready"
                            ]
                        )
                    ),
                    "r12_recall_mitigation_external_or_customer_product_default_allowed": (
                        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
                is not None
                else {}
            ),
            **(
                {
                    "r12_external_or_customer_raw_slice_present": (
                        r12_external_or_customer_holdout_raw_slice[
                            "acceptance_gates"
                        ]["raw_external_or_customer_slice_present"]
                    ),
                    "r12_external_or_customer_actual_public_data_ingested": (
                        r12_external_or_customer_holdout_raw_slice[
                            "acceptance_gates"
                        ]["actual_public_data_ingested"]
                    ),
                    "r12_external_or_customer_revalidation_ready": (
                        r12_external_or_customer_holdout_raw_slice[
                            "acceptance_gates"
                        ]["external_holdout_revalidation_ready"]
                    ),
                    "r12_external_or_customer_product_default_allowed": (
                        r12_external_or_customer_holdout_raw_slice[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_external_or_customer_holdout_raw_slice is not None
                else {}
            ),
            **(
                {
                    "r12_external_holdout_revalidation_executed": (
                        r12_recall_mitigation_external_holdout_revalidation[
                            "acceptance_gates"
                        ]["external_holdout_revalidation_executed"]
                    ),
                    "r12_external_holdout_revalidation_passed": (
                        r12_recall_mitigation_external_holdout_revalidation[
                            "acceptance_gates"
                        ]["external_holdout_revalidation_passed"]
                    ),
                    "r12_external_holdout_prediction_independent": (
                        r12_recall_mitigation_external_holdout_revalidation[
                            "acceptance_gates"
                        ][
                            "prediction_source_independent_of_observed_outcome"
                        ]
                    ),
                    "r12_external_holdout_false_alarm_non_regression": (
                        r12_recall_mitigation_external_holdout_revalidation[
                            "acceptance_gates"
                        ]["false_alarm_non_regression"]
                    ),
                    "r12_external_holdout_product_default_allowed": (
                        r12_recall_mitigation_external_holdout_revalidation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_recall_mitigation_external_holdout_revalidation
                is not None
                else {}
            ),
            **(
                {
                    "r12_pre_outcome_or_independent_prediction_packet_generated": (
                        r12_pre_outcome_or_independent_prediction_packet[
                            "acceptance_gates"
                        ]["prediction_packet_generated"]
                    ),
                    "r12_prediction_source_independent_of_target_outcome": (
                        r12_pre_outcome_or_independent_prediction_packet[
                            "acceptance_gates"
                        ][
                            "prediction_source_independent_of_target_outcome"
                        ]
                    ),
                    "r12_prediction_lock_timestamp_pre_target_outcome": (
                        r12_pre_outcome_or_independent_prediction_packet[
                            "acceptance_gates"
                        ]["prediction_lock_timestamp_pre_target_outcome"]
                    ),
                    "r12_hindcast_independent_revalidation_ready": (
                        r12_pre_outcome_or_independent_prediction_packet[
                            "acceptance_gates"
                        ]["hindcast_independent_revalidation_ready"]
                    ),
                    "r12_pre_outcome_revalidation_ready": (
                        r12_pre_outcome_or_independent_prediction_packet[
                            "acceptance_gates"
                        ]["pre_outcome_revalidation_ready"]
                    ),
                    "r12_pre_outcome_or_independent_prediction_product_default_allowed": (
                        r12_pre_outcome_or_independent_prediction_packet[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_pre_outcome_or_independent_prediction_packet is not None
                else {}
            ),
            **(
                {
                    "r12_independent_hindcast_revalidation_executed": (
                        r12_independent_hindcast_revalidation[
                            "acceptance_gates"
                        ]["hindcast_independent_revalidation_executed"]
                    ),
                    "r12_independent_hindcast_revalidation_passed": (
                        r12_independent_hindcast_revalidation[
                            "acceptance_gates"
                        ]["hindcast_independent_revalidation_passed"]
                    ),
                    "r12_independent_hindcast_false_alarm_non_regression": (
                        r12_independent_hindcast_revalidation[
                            "acceptance_gates"
                        ]["false_alarm_non_regression"]
                    ),
                    "r12_independent_hindcast_pre_outcome_ready": (
                        r12_independent_hindcast_revalidation[
                            "acceptance_gates"
                        ]["pre_outcome_revalidation_ready"]
                    ),
                    "r12_independent_hindcast_product_default_allowed": (
                        r12_independent_hindcast_revalidation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_independent_hindcast_revalidation is not None
                else {}
            ),
            **(
                {
                    "r12_pre_outcome_prediction_trial_created": (
                        r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                            "acceptance_gates"
                        ]["pre_outcome_prediction_trial_created"]
                    ),
                    "r12_pre_outcome_prediction_packet_locked": (
                        r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                            "acceptance_gates"
                        ]["prediction_packet_locked"]
                    ),
                    "r12_pre_outcome_prediction_lock_pre_target_outcome": (
                        r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                            "acceptance_gates"
                        ]["prediction_lock_timestamp_pre_target_outcome"]
                    ),
                    "r12_pre_outcome_target_outcome_artifact_present": (
                        r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                            "acceptance_gates"
                        ]["target_outcome_artifact_present"]
                    ),
                    "r12_customer_field_slice_contract_ready": (
                        r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                            "acceptance_gates"
                        ]["customer_field_slice_contract_ready"]
                    ),
                    "r12_pre_outcome_or_customer_field_product_default_allowed": (
                        r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_pre_outcome_prediction_trial_or_customer_field_revalidation
                is not None
                else {}
            ),
            **(
                {
                    "r12_outcome_ingestion_target_public_outcome_available": (
                        r12_pre_outcome_or_customer_field_outcome_ingestion[
                            "acceptance_gates"
                        ]["target_public_outcome_available"]
                    ),
                    "r12_outcome_ingestion_target_outcome_artifact_present": (
                        r12_pre_outcome_or_customer_field_outcome_ingestion[
                            "acceptance_gates"
                        ]["target_outcome_artifact_present"]
                    ),
                    "r12_outcome_ingestion_customer_field_slice_contract_ready": (
                        r12_pre_outcome_or_customer_field_outcome_ingestion[
                            "acceptance_gates"
                        ]["customer_field_slice_contract_ready"]
                    ),
                    "r12_outcome_ingestion_revalidation_ready": (
                        r12_pre_outcome_or_customer_field_outcome_ingestion[
                            "acceptance_gates"
                        ]["field_or_pre_outcome_revalidation_ready"]
                    ),
                    "r12_outcome_ingestion_product_default_allowed": (
                        r12_pre_outcome_or_customer_field_outcome_ingestion[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_pre_outcome_or_customer_field_outcome_ingestion is not None
                else {}
            ),
            **(
                {
                    "r12_outcome_revalidation_metrics_computed": (
                        r12_pre_outcome_or_customer_field_outcome_revalidation[
                            "acceptance_gates"
                        ]["metrics_computed"]
                    ),
                    "r12_outcome_revalidation_ready": (
                        r12_pre_outcome_or_customer_field_outcome_revalidation[
                            "acceptance_gates"
                        ]["field_or_pre_outcome_revalidation_ready"]
                    ),
                    "r12_outcome_revalidation_passed": (
                        r12_pre_outcome_or_customer_field_outcome_revalidation[
                            "acceptance_gates"
                        ]["field_or_pre_outcome_revalidation_passed"]
                    ),
                    "r12_outcome_revalidation_product_default_allowed": (
                        r12_pre_outcome_or_customer_field_outcome_revalidation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_pre_outcome_or_customer_field_outcome_revalidation
                is not None
                else {}
            ),
            **(
                {
                    "r12_target_or_customer_slice_arrival_source_arrived": (
                        r12_target_outcome_or_customer_field_slice_arrival[
                            "acceptance_gates"
                        ]["outcome_source_arrived"]
                    ),
                    "r12_target_or_customer_slice_arrival_revalidation_ready": (
                        r12_target_outcome_or_customer_field_slice_arrival[
                            "acceptance_gates"
                        ]["field_or_pre_outcome_revalidation_ready"]
                    ),
                    "r12_target_or_customer_slice_arrival_metrics_computed": (
                        r12_target_outcome_or_customer_field_slice_arrival[
                            "acceptance_gates"
                        ]["metrics_computed"]
                    ),
                    "r12_target_or_customer_slice_arrival_product_default_allowed": (
                        r12_target_outcome_or_customer_field_slice_arrival[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_target_outcome_or_customer_field_slice_arrival is not None
                else {}
            ),
            **(
                {
                    "r12_customer_field_slice_handoff_template_generated": (
                        r12_customer_field_slice_handoff_package[
                            "acceptance_gates"
                        ]["customer_field_slice_template_generated"]
                    ),
                    "r12_customer_field_slice_handoff_data_request_ready": (
                        r12_customer_field_slice_handoff_package[
                            "acceptance_gates"
                        ]["customer_data_request_ready"]
                    ),
                    "r12_customer_field_slice_handoff_metrics_computed": (
                        r12_customer_field_slice_handoff_package[
                            "acceptance_gates"
                        ]["metrics_computed"]
                    ),
                    "r12_customer_field_slice_handoff_product_default_allowed": (
                        r12_customer_field_slice_handoff_package[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_field_slice_handoff_package is not None
                else {}
            ),
            **(
                {
                    "r12_customer_field_slice_intake_ready_for_revalidation": (
                        r12_customer_field_slice_intake_validation[
                            "acceptance_gates"
                        ]["ready_for_revalidation"]
                    ),
                    "r12_customer_field_slice_intake_metrics_computed": (
                        r12_customer_field_slice_intake_validation[
                            "acceptance_gates"
                        ]["metrics_computed"]
                    ),
                    "r12_customer_field_slice_intake_product_default_allowed": (
                        r12_customer_field_slice_intake_validation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_field_slice_intake_validation is not None
                else {}
            ),
            **(
                {
                    "r12_customer_field_slice_revalidation_metrics_computed": (
                        r12_customer_field_slice_revalidation[
                            "acceptance_gates"
                        ]["metrics_computed"]
                    ),
                    "r12_customer_field_slice_revalidation_field_outcome_validated": (
                        r12_customer_field_slice_revalidation[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_field_slice_revalidation_product_default_allowed": (
                        r12_customer_field_slice_revalidation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_field_slice_revalidation is not None
                else {}
            ),
            **(
                {
                    "r12_customer_field_feedback_update_candidate_count": (
                        r12_customer_field_outcome_feedback_update[
                            "feedback_summary"
                        ]["candidate_count"]
                    ),
                    "r12_customer_field_feedback_update_metrics_consumed": (
                        r12_customer_field_outcome_feedback_update[
                            "acceptance_gates"
                        ]["metrics_consumed"]
                    ),
                    "r12_customer_field_feedback_update_product_default_allowed": (
                        r12_customer_field_outcome_feedback_update[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_field_outcome_feedback_update is not None
                else {}
            ),
            **(
                {
                    "r12_customer_feedback_shadow_replay_executed": (
                        r12_customer_feedback_update_shadow_replay[
                            "acceptance_gates"
                        ]["shadow_replay_executed"]
                    ),
                    "r12_customer_feedback_shadow_replay_accepted_candidate_count": (
                        r12_customer_feedback_update_shadow_replay[
                            "shadow_replay_summary"
                        ]["accepted_candidate_count"]
                    ),
                    "r12_customer_feedback_shadow_replay_product_default_allowed": (
                        r12_customer_feedback_update_shadow_replay[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_feedback_update_shadow_replay is not None
                else {}
            ),
            **(
                {
                    "r12_customer_feedback_holdout_review_executed": (
                        r12_customer_feedback_shadow_replay_holdout_review[
                            "acceptance_gates"
                        ]["holdout_review_executed"]
                    ),
                    "r12_customer_feedback_holdout_review_passed": (
                        r12_customer_feedback_shadow_replay_holdout_review[
                            "acceptance_gates"
                        ]["holdout_review_passed"]
                    ),
                    "r12_customer_feedback_holdout_review_product_default_allowed": (
                        r12_customer_feedback_shadow_replay_holdout_review[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_feedback_shadow_replay_holdout_review
                is not None
                else {}
            ),
            **(
                {
                    "r12_customer_validation_workflow_status_package_ready": (
                        r12_customer_validation_workflow_status[
                            "acceptance_gates"
                        ]["workflow_status_package_ready"]
                    ),
                    "r12_customer_validation_workflow_field_outcome_validated": (
                        r12_customer_validation_workflow_status[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_validation_workflow_product_default_allowed": (
                        r12_customer_validation_workflow_status[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_validation_workflow_status is not None
                else {}
            ),
            **(
                {
                    "r12_customer_trial_readiness_package_ready": (
                        r12_customer_trial_readiness_package[
                            "acceptance_gates"
                        ]["trial_readiness_package_ready"]
                    ),
                    "r12_customer_trial_readiness_field_outcome_validated": (
                        r12_customer_trial_readiness_package[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_trial_readiness_product_default_allowed": (
                        r12_customer_trial_readiness_package[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_trial_readiness_package is not None
                else {}
            ),
            **(
                {
                    "r12_customer_trial_operational_check_ready": (
                        r12_customer_trial_operational_check[
                            "acceptance_gates"
                        ]["trial_readiness_package_loaded"]
                    ),
                    "r12_customer_trial_operationally_ready": (
                        r12_customer_trial_operational_check[
                            "acceptance_gates"
                        ]["customer_trial_request_operationally_ready"]
                    ),
                    "r12_customer_trial_operational_field_outcome_validated": (
                        r12_customer_trial_operational_check[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_trial_operational_product_default_allowed": (
                        r12_customer_trial_operational_check[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_trial_operational_check is not None
                else {}
            ),
            **(
                {
                    "r12_customer_trial_launch_handoff_package_ready": (
                        r12_customer_trial_launch_handoff_package[
                            "acceptance_gates"
                        ]["launch_handoff_package_ready"]
                    ),
                    "r12_customer_trial_launch_handoff_field_outcome_validated": (
                        r12_customer_trial_launch_handoff_package[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_trial_launch_handoff_product_default_allowed": (
                        r12_customer_trial_launch_handoff_package[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_trial_launch_handoff_package is not None
                else {}
            ),
            **(
                {
                    "r12_customer_trial_launch_packet_export_ready": (
                        r12_customer_trial_launch_packet_export[
                            "acceptance_gates"
                        ]["launch_packet_export_ready"]
                    ),
                    "r12_customer_trial_launch_packet_field_outcome_validated": (
                        r12_customer_trial_launch_packet_export[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_trial_launch_packet_product_default_allowed": (
                        r12_customer_trial_launch_packet_export[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_trial_launch_packet_export is not None
                else {}
            ),
            **(
                {
                    "r12_customer_trial_launch_bundle_verified": (
                        r12_customer_trial_launch_bundle_verification[
                            "acceptance_gates"
                        ]["launch_bundle_verified"]
                    ),
                    "r12_customer_trial_launch_bundle_field_outcome_validated": (
                        r12_customer_trial_launch_bundle_verification[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_trial_launch_bundle_product_default_allowed": (
                        r12_customer_trial_launch_bundle_verification[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_trial_launch_bundle_verification is not None
                else {}
            ),
            **(
                {
                    "r12_customer_field_slice_operator_rehearsed": (
                        r12_customer_field_slice_operator_rehearsal[
                            "acceptance_gates"
                        ]["operator_command_rehearsed"]
                    ),
                    "r12_customer_field_slice_operator_real_customer_slice_submitted": (
                        r12_customer_field_slice_operator_rehearsal[
                            "acceptance_gates"
                        ]["real_customer_field_slice_submitted"]
                    ),
                    "r12_customer_field_slice_operator_product_default_allowed": (
                        r12_customer_field_slice_operator_rehearsal[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_field_slice_operator_rehearsal is not None
                else {}
            ),
            **(
                {
                    "r12_customer_feedback_loop_rehearsed_l22_to_l26": (
                        r12_customer_feedback_loop_operator_rehearsal[
                            "acceptance_gates"
                        ]["l22_intake_validator_executed"]
                        and r12_customer_feedback_loop_operator_rehearsal[
                            "acceptance_gates"
                        ]["l23_field_revalidation_executed"]
                        and r12_customer_feedback_loop_operator_rehearsal[
                            "acceptance_gates"
                        ]["l24_feedback_candidates_generated"]
                        and r12_customer_feedback_loop_operator_rehearsal[
                            "acceptance_gates"
                        ]["l25_shadow_replay_executed"]
                        and r12_customer_feedback_loop_operator_rehearsal[
                            "acceptance_gates"
                        ]["l26_synthetic_holdout_review_executed"]
                    ),
                    "r12_customer_feedback_loop_real_customer_slice_submitted": (
                        r12_customer_feedback_loop_operator_rehearsal[
                            "acceptance_gates"
                        ]["real_customer_field_slice_submitted"]
                    ),
                    "r12_customer_feedback_loop_product_default_allowed": (
                        r12_customer_feedback_loop_operator_rehearsal[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_feedback_loop_operator_rehearsal is not None
                else {}
            ),
            **(
                {
                    "r12_customer_trial_evidence_ledger_ready": (
                        r12_customer_trial_evidence_ledger[
                            "acceptance_gates"
                        ]["customer_trial_evidence_ledger_ready"]
                    ),
                    "r12_customer_trial_evidence_ledger_field_outcome_validated": (
                        r12_customer_trial_evidence_ledger[
                            "acceptance_gates"
                        ]["field_outcome_validated"]
                    ),
                    "r12_customer_trial_evidence_ledger_product_default_allowed": (
                        r12_customer_trial_evidence_ledger[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_customer_trial_evidence_ledger is not None
                else {}
            ),
        },
        "source_registry": _source_registry(
            r12_transfer_validation=r12_transfer_validation,
            r12_high_risk_holdout_registry=r12_high_risk_holdout_registry,
            r12_high_risk_holdout_transfer_replay=(
                r12_high_risk_holdout_transfer_replay
            ),
            r12_recall_oriented_update=r12_recall_oriented_update,
            r12_recall_update_false_alarm_stress_test=(
                r12_recall_update_false_alarm_stress_test
            ),
            r12_recall_false_alarm_mitigation_candidate=(
                r12_recall_false_alarm_mitigation_candidate
            ),
            r12_recall_mitigation_holdout_validation=(
                r12_recall_mitigation_holdout_validation
            ),
            r12_recall_mitigation_independent_holdout_data=(
                r12_recall_mitigation_independent_holdout_data
            ),
            r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
                r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
            ),
            r12_external_or_customer_holdout_raw_slice=(
                r12_external_or_customer_holdout_raw_slice
            ),
            r12_recall_mitigation_external_holdout_revalidation=(
                r12_recall_mitigation_external_holdout_revalidation
            ),
            r12_pre_outcome_or_independent_prediction_packet=(
                r12_pre_outcome_or_independent_prediction_packet
            ),
            r12_independent_hindcast_revalidation=(
                r12_independent_hindcast_revalidation
            ),
            r12_pre_outcome_prediction_trial_or_customer_field_revalidation=(
                r12_pre_outcome_prediction_trial_or_customer_field_revalidation
            ),
            r12_pre_outcome_or_customer_field_outcome_ingestion=(
                r12_pre_outcome_or_customer_field_outcome_ingestion
            ),
            r12_pre_outcome_or_customer_field_outcome_revalidation=(
                r12_pre_outcome_or_customer_field_outcome_revalidation
            ),
            r12_target_outcome_or_customer_field_slice_arrival=(
                r12_target_outcome_or_customer_field_slice_arrival
            ),
            r12_customer_field_slice_handoff_package=(
                r12_customer_field_slice_handoff_package
            ),
            r12_customer_field_slice_intake_validation=(
                r12_customer_field_slice_intake_validation
            ),
            r12_customer_field_slice_revalidation=(
                r12_customer_field_slice_revalidation
            ),
            r12_customer_field_outcome_feedback_update=(
                r12_customer_field_outcome_feedback_update
            ),
            r12_customer_feedback_update_shadow_replay=(
                r12_customer_feedback_update_shadow_replay
            ),
            r12_customer_feedback_shadow_replay_holdout_review=(
                r12_customer_feedback_shadow_replay_holdout_review
            ),
            r12_customer_validation_workflow_status=(
                r12_customer_validation_workflow_status
            ),
            r12_customer_trial_readiness_package=(
                r12_customer_trial_readiness_package
            ),
            r12_customer_trial_operational_check=(
                r12_customer_trial_operational_check
            ),
            r12_customer_trial_launch_handoff_package=(
                r12_customer_trial_launch_handoff_package
            ),
            r12_customer_trial_launch_packet_export=(
                r12_customer_trial_launch_packet_export
            ),
            r12_customer_trial_launch_bundle_verification=(
                r12_customer_trial_launch_bundle_verification
            ),
            r12_customer_field_slice_operator_rehearsal=(
                r12_customer_field_slice_operator_rehearsal
            ),
            r12_customer_feedback_loop_operator_rehearsal=(
                r12_customer_feedback_loop_operator_rehearsal
            ),
            r12_customer_trial_evidence_ledger=(
                r12_customer_trial_evidence_ledger
            ),
        ),
        "source_refs": [
            r12_transfer_validation["artifact_id"],
            *(
                [r12_high_risk_holdout_registry["artifact_id"]]
                if r12_high_risk_holdout_registry is not None
                else []
            ),
            *(
                [r12_high_risk_holdout_transfer_replay["artifact_id"]]
                if r12_high_risk_holdout_transfer_replay is not None
                else []
            ),
            *(
                [r12_recall_oriented_update["artifact_id"]]
                if r12_recall_oriented_update is not None
                else []
            ),
            *(
                [r12_recall_update_false_alarm_stress_test["artifact_id"]]
                if r12_recall_update_false_alarm_stress_test is not None
                else []
            ),
            *(
                [r12_recall_false_alarm_mitigation_candidate["artifact_id"]]
                if r12_recall_false_alarm_mitigation_candidate is not None
                else []
            ),
            *(
                [r12_recall_mitigation_holdout_validation["artifact_id"]]
                if r12_recall_mitigation_holdout_validation is not None
                else []
            ),
            *(
                [r12_recall_mitigation_independent_holdout_data["artifact_id"]]
                if r12_recall_mitigation_independent_holdout_data is not None
                else []
            ),
            *(
                [
                    r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                        "artifact_id"
                    ]
                ]
                if r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
                is not None
                else []
            ),
            *(
                [r12_external_or_customer_holdout_raw_slice["artifact_id"]]
                if r12_external_or_customer_holdout_raw_slice is not None
                else []
            ),
            *(
                [
                    r12_recall_mitigation_external_holdout_revalidation[
                        "artifact_id"
                    ]
                ]
                if r12_recall_mitigation_external_holdout_revalidation
                is not None
                else []
            ),
            *(
                [
                    r12_pre_outcome_or_independent_prediction_packet[
                        "artifact_id"
                    ]
                ]
                if r12_pre_outcome_or_independent_prediction_packet is not None
                else []
            ),
            *(
                [r12_independent_hindcast_revalidation["artifact_id"]]
                if r12_independent_hindcast_revalidation is not None
                else []
            ),
            *(
                [
                    r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                        "artifact_id"
                    ]
                ]
                if r12_pre_outcome_prediction_trial_or_customer_field_revalidation
                is not None
                else []
            ),
            *(
                [
                    r12_pre_outcome_or_customer_field_outcome_ingestion[
                        "artifact_id"
                    ]
                ]
                if r12_pre_outcome_or_customer_field_outcome_ingestion is not None
                else []
            ),
            *(
                [
                    r12_pre_outcome_or_customer_field_outcome_revalidation[
                        "artifact_id"
                    ]
                ]
                if r12_pre_outcome_or_customer_field_outcome_revalidation
                is not None
                else []
            ),
            *(
                [
                    r12_target_outcome_or_customer_field_slice_arrival[
                        "artifact_id"
                    ]
                ]
                if r12_target_outcome_or_customer_field_slice_arrival is not None
                else []
            ),
            *(
                [r12_customer_field_slice_handoff_package["artifact_id"]]
                if r12_customer_field_slice_handoff_package is not None
                else []
            ),
            *(
                [r12_customer_field_slice_intake_validation["artifact_id"]]
                if r12_customer_field_slice_intake_validation is not None
                else []
            ),
            *(
                [r12_customer_field_slice_revalidation["artifact_id"]]
                if r12_customer_field_slice_revalidation is not None
                else []
            ),
            *(
                [r12_customer_field_outcome_feedback_update["artifact_id"]]
                if r12_customer_field_outcome_feedback_update is not None
                else []
            ),
            *(
                [r12_customer_feedback_update_shadow_replay["artifact_id"]]
                if r12_customer_feedback_update_shadow_replay is not None
                else []
            ),
            *(
                [
                    r12_customer_feedback_shadow_replay_holdout_review[
                        "artifact_id"
                    ]
                ]
                if r12_customer_feedback_shadow_replay_holdout_review
                is not None
                else []
            ),
            *(
                [r12_customer_validation_workflow_status["artifact_id"]]
                if r12_customer_validation_workflow_status is not None
                else []
            ),
            *(
                [r12_customer_trial_readiness_package["artifact_id"]]
                if r12_customer_trial_readiness_package is not None
                else []
            ),
            *(
                [r12_customer_trial_operational_check["artifact_id"]]
                if r12_customer_trial_operational_check is not None
                else []
            ),
            *(
                [r12_customer_trial_launch_handoff_package["artifact_id"]]
                if r12_customer_trial_launch_handoff_package is not None
                else []
            ),
            *(
                [r12_customer_trial_launch_packet_export["artifact_id"]]
                if r12_customer_trial_launch_packet_export is not None
                else []
            ),
            *(
                [r12_customer_trial_launch_bundle_verification["artifact_id"]]
                if r12_customer_trial_launch_bundle_verification is not None
                else []
            ),
            *(
                [r12_customer_field_slice_operator_rehearsal["artifact_id"]]
                if r12_customer_field_slice_operator_rehearsal is not None
                else []
            ),
            *(
                [r12_customer_feedback_loop_operator_rehearsal["artifact_id"]]
                if r12_customer_feedback_loop_operator_rehearsal is not None
                else []
            ),
            *(
                [r12_customer_trial_evidence_ledger["artifact_id"]]
                if r12_customer_trial_evidence_ledger is not None
                else []
            ),
        ],
        "allowed_claims": [
            (
                "Product can display R12 as a source-backed guarded transfer "
                "evidence card."
            ),
            (
                "R12 transfer evidence is secondary and requires customer or "
                "field outcome review before any runtime-default update."
            ),
            *(
                [
                    (
                        "R12 has tested effective on public data under guarded "
                        "hindcast metrics."
                    )
                ]
                if public_data_effectiveness_claim_allowed
                else []
            ),
            *(
                [
                    (
                        "R12 has research-only high-risk holdout candidates, but "
                        "Product default use remains blocked until low-sensitive "
                        "or customer-approved holdout validation exists."
                    )
                ]
                if r12_high_risk_holdout_registry is not None
                else []
            ),
            *(
                [
                    (
                        "R12 recall-oriented activation margin can be shown as a "
                        "research-only improvement with explicit false-alarm and "
                        "precision tradeoff."
                    )
                ]
                if r12_recall_oriented_update is not None
                else []
            ),
            *(
                [
                    (
                        "R12 recall-oriented update has a source-backed "
                        "false-alarm stress boundary and remains Product-default "
                        "blocked."
                    )
                ]
                if r12_recall_update_false_alarm_stress_test is not None
                else []
            ),
            *(
                [
                    (
                        "R12 false-alarm mitigation can be shown as a research-only "
                        "candidate, but it needs independent holdout validation."
                    )
                ]
                if r12_recall_false_alarm_mitigation_candidate is not None
                else []
            ),
            *(
                [
                    (
                        "R12 mitigation holdout validation blocks Product default "
                        "and preserves the candidate as failure diagnosis evidence."
                    )
                ]
                if r12_recall_mitigation_holdout_validation is not None
                else []
            ),
            *(
                [
                    (
                        "R12 independent holdout data audit can be shown as a "
                        "Product evidence boundary, while Product default remains blocked."
                    )
                ]
                if r12_recall_mitigation_independent_holdout_data is not None
                else []
            ),
            *(
                [
                    (
                        "R12 external-or-customer holdout ingestion contract is "
                        "ready, but raw slice and revalidation are still required."
                    )
                ]
                if r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
                is not None
                else []
            ),
            *(
                [
                    (
                        "R12 has ingested a DOT ATCR official raw complaint slice "
                        "for external holdout revalidation preparation."
                    )
                ]
                if r12_external_or_customer_holdout_raw_slice is not None
                else []
            ),
            *(
                [
                    (
                        "R12 external holdout revalidation proxy metrics can be "
                        "shown as diagnostic evidence, while independent prediction "
                        "validation remains blocked."
                    )
                ]
                if r12_recall_mitigation_external_holdout_revalidation
                is not None
                else []
            ),
            *(
                [
                    (
                        "R12 has an independent prior-month prediction packet "
                        "ready for hindcast revalidation, but it is not a "
                        "pre-outcome locked packet."
                    )
                ]
                if r12_pre_outcome_or_independent_prediction_packet is not None
                else []
            ),
            *(
                [
                    (
                        "R12 independent hindcast revalidation shows positive "
                        "diagnostic improvement over the static prior, but "
                        "pre-outcome or field validation is still required."
                    )
                ]
                if r12_independent_hindcast_revalidation is not None
                else []
            ),
            *(
                [
                    (
                        "R12 has locked a pre-outcome prediction trial and "
                        "defined a customer field revalidation contract, but "
                        "outcome validation is still pending."
                    )
                ]
                if r12_pre_outcome_prediction_trial_or_customer_field_revalidation
                is not None
                else []
            ),
            *(
                [
                    (
                        "R12 outcome ingestion records that the public target "
                        "outcome is still pending and the customer field slice "
                        "contract is ready."
                    )
                ]
                if r12_pre_outcome_or_customer_field_outcome_ingestion is not None
                else []
            ),
            *(
                [
                    (
                        "R12 outcome revalidation harness is fail-closed and "
                        "ready to run once target outcome or customer field "
                        "slice arrives."
                    )
                ]
                if r12_pre_outcome_or_customer_field_outcome_revalidation
                is not None
                else []
            ),
            *(
                [
                    (
                        "R12 target outcome/customer field slice arrival gate "
                        "is ready and keeps Product default blocked until "
                        "revalidation metrics are computed."
                    )
                ]
                if r12_target_outcome_or_customer_field_slice_arrival is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer field slice handoff package is ready for "
                        "customer data collection, while validation and Product "
                        "default remain blocked."
                    )
                ]
                if r12_customer_field_slice_handoff_package is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer field feedback update can generate "
                        "bounded shadow-review candidates from validated field "
                        "metrics, while Product default remains blocked."
                    )
                ]
                if r12_customer_field_outcome_feedback_update is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer feedback shadow replay can evaluate "
                        "bounded update candidates, while Product default "
                        "remains blocked."
                    )
                ]
                if r12_customer_feedback_update_shadow_replay is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer feedback holdout review can gate shadow "
                        "candidates against independent/customer-approved "
                        "holdout evidence, while Product default remains blocked."
                    )
                ]
                if r12_customer_feedback_shadow_replay_holdout_review
                is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer validation workflow can show the "
                        "current validation stage and operator runbook, while "
                        "Product default remains blocked."
                    )
                ]
                if r12_customer_validation_workflow_status is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer trial readiness package can provide a "
                        "source-backed trial checklist and operator runbook, "
                        "while Product default remains blocked."
                    )
                ]
                if r12_customer_trial_readiness_package is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer trial operational check verifies "
                        "template, source registry, and operator runbook, "
                        "while field validation remains pending."
                    )
                ]
                if r12_customer_trial_operational_check is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer trial launch handoff package can provide "
                        "a customer-facing data request and submission runbook, "
                        "while Product default remains blocked."
                    )
                ]
                if r12_customer_trial_launch_handoff_package is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer trial launch packet export can provide "
                        "a customer-readable Markdown handoff packet, while "
                        "Product default remains blocked."
                    )
                ]
                if r12_customer_trial_launch_packet_export is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer trial launch bundle verification can "
                        "prove launch packet, handoff, and template files are "
                        "resolvable, while Product default remains blocked."
                    )
                ]
                if r12_customer_trial_launch_bundle_verification is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer field slice operator rehearsal can prove "
                        "the intake command is executable on a synthetic "
                        "fixture, while customer validation remains blocked."
                    )
                ]
                if r12_customer_field_slice_operator_rehearsal is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer feedback loop rehearsal can prove "
                        "L22-L26 are executable on a synthetic fixture, while "
                        "real field validation remains blocked."
                    )
                ]
                if r12_customer_feedback_loop_operator_rehearsal is not None
                else []
            ),
            *(
                [
                    (
                        "R12 customer trial evidence ledger can show a "
                        "source-backed trial-readiness audit trail, while "
                        "real field validation remains blocked."
                    )
                ]
                if r12_customer_trial_evidence_ledger is not None
                else []
            ),
        ],
        "blocked_claims": _resolved_blocked_claims(
            [
                "R12 validated",
                "R12 supports Product core method by default",
                "R12 can override guarded baseline primary decision",
                "R12 Product default high-risk recovery validated",
                "static-prior miss recovery improved on high-risk replay",
                "abnormal segment recall improved on high-risk replay",
                "field_outcome_validated=true",
                "runtime_default_allowed=true",
                "runtime default ready",
                "customer field outcome validated",
                "精准预测系统",
                *(r12_recall_oriented_update or {}).get("blocked_claims", []),
                *(r12_recall_update_false_alarm_stress_test or {}).get(
                    "blocked_claims", []
                ),
                *(r12_recall_false_alarm_mitigation_candidate or {}).get(
                    "blocked_claims", []
                ),
                *(r12_recall_mitigation_holdout_validation or {}).get(
                    "blocked_claims", []
                ),
                *(r12_recall_mitigation_independent_holdout_data or {}).get(
                    "blocked_claims", []
                ),
                *(
                    r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
                    or {}
                ).get("blocked_claims", []),
                *(r12_external_or_customer_holdout_raw_slice or {}).get(
                    "blocked_claims", []
                ),
                *(
                    r12_recall_mitigation_external_holdout_revalidation
                    or {}
                ).get("blocked_claims", []),
                *(
                    r12_pre_outcome_or_independent_prediction_packet or {}
                ).get("blocked_claims", []),
                *(
                    r12_independent_hindcast_revalidation or {}
                ).get("blocked_claims", []),
                *(
                    r12_pre_outcome_prediction_trial_or_customer_field_revalidation
                    or {}
                ).get("blocked_claims", []),
                *(
                    r12_pre_outcome_or_customer_field_outcome_ingestion or {}
                ).get("blocked_claims", []),
                *(
                    r12_pre_outcome_or_customer_field_outcome_revalidation
                    or {}
                ).get("blocked_claims", []),
                *(
                    r12_target_outcome_or_customer_field_slice_arrival or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_field_slice_handoff_package or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_field_slice_intake_validation or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_field_slice_revalidation or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_field_outcome_feedback_update or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_feedback_update_shadow_replay or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_feedback_shadow_replay_holdout_review or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_validation_workflow_status or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_trial_readiness_package or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_trial_operational_check or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_trial_launch_handoff_package or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_trial_launch_packet_export or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_trial_launch_bundle_verification or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_field_slice_operator_rehearsal or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_feedback_loop_operator_rehearsal or {}
                ).get("blocked_claims", []),
                *(
                    r12_customer_trial_evidence_ledger or {}
                ).get("blocked_claims", []),
            ],
            r12_external_or_customer_holdout_raw_slice=(
                r12_external_or_customer_holdout_raw_slice
            ),
            r12_recall_mitigation_external_holdout_revalidation=(
                r12_recall_mitigation_external_holdout_revalidation
            ),
        ),
    }
    if r12_high_risk_holdout_registry is None:
        report["blocked_claims"] = [
            item
            for item in report["blocked_claims"]
            if item != "R12 Product default high-risk recovery validated"
            and item != "static-prior miss recovery improved on high-risk replay"
            and item != "abnormal segment recall improved on high-risk replay"
        ]
    assert_strict_json(report)
    return report


def write_r12_product_support_gate(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_product_support_gate(**kwargs))


def _validate_transfer_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_TRANSFER_VALIDATION_SCHEMA_VERSION:
        raise ValueError(
            "r12_transfer_validation.schema_version must be "
            f"{R12_TRANSFER_VALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_transfer_validation.acceptance_gates must be an object")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 transfer validation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 transfer validation must not allow runtime default")
    if gates.get("train_metrics_used_for_transfer_decision") is not False:
        raise ValueError("r12 transfer validation must not use train metrics as proof")


def _validate_high_risk_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION:
        raise ValueError(
            "r12_high_risk_holdout_registry.schema_version must be "
            f"{R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 high-risk holdout registry acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 high-risk registry must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 high-risk registry must not allow runtime default")


def _validate_high_risk_replay(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION:
        raise ValueError(
            "r12_high_risk_holdout_transfer_replay.schema_version must be "
            f"{R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 high-risk replay acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 high-risk replay must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 high-risk replay must not allow runtime default")


def _validate_recall_oriented_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION:
        raise ValueError(
            "r12_recall_oriented_update.schema_version must be "
            f"{R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 recall-oriented update acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 recall-oriented update must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 recall-oriented update must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 recall-oriented update must not allow Product default")


def _validate_recall_false_alarm_stress(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_update_false_alarm_stress_test.schema_version must be "
            f"{R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 false-alarm stress acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 false-alarm stress must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 false-alarm stress must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 false-alarm stress must not allow Product default")


def _validate_recall_false_alarm_mitigation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_false_alarm_mitigation_candidate.schema_version must be "
            f"{R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 false-alarm mitigation acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 false-alarm mitigation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 false-alarm mitigation must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 false-alarm mitigation must not allow Product default")


def _validate_recall_mitigation_holdout_validation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_mitigation_holdout_validation.schema_version must be "
            f"{R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 mitigation holdout validation acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 mitigation holdout validation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 mitigation holdout validation must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 mitigation holdout validation must not allow Product default")


def _validate_recall_mitigation_independent_holdout_data(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_mitigation_independent_holdout_data.schema_version must be "
            f"{R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 independent holdout data acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 independent holdout data must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 independent holdout data must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 independent holdout data must not allow Product default")


def _validate_recall_mitigation_external_holdout_ingestion_or_customer_slice(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice."
            "schema_version must be "
            f"{R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 external/customer slice acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 external/customer slice must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 external/customer slice must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 external/customer slice must not allow Product default")


def _validate_external_or_customer_holdout_raw_slice(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_external_or_customer_holdout_raw_slice.schema_version must be "
            f"{R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 raw slice acceptance_gates required")
    if gates.get("raw_external_or_customer_slice_present") is not True:
        raise ValueError("r12 raw slice must be present")
    if gates.get("actual_public_data_ingested") is not True:
        raise ValueError("r12 raw slice must ingest actual public data")
    if gates.get("external_holdout_revalidation_ready") is not False:
        raise ValueError("r12 raw slice must keep revalidation pending")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 raw slice must not allow Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 raw slice must not allow runtime default")


def _validate_recall_mitigation_external_holdout_revalidation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_mitigation_external_holdout_revalidation.schema_version "
            "must be "
            f"{R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 external revalidation acceptance_gates required")
    if gates.get("prediction_fields_generated") is not True:
        raise ValueError("r12 external revalidation must generate predictions")
    if gates.get("external_holdout_revalidation_executed") is not True:
        raise ValueError("r12 external revalidation must execute")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 external revalidation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 external revalidation must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 external revalidation must not allow Product default")


def _validate_pre_outcome_or_independent_prediction_packet(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_pre_outcome_or_independent_prediction_packet.schema_version "
            "must be "
            f"{R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 prediction packet acceptance_gates required")
    if gates.get("prediction_packet_generated") is not True:
        raise ValueError("r12 prediction packet must be generated")
    if gates.get("prediction_source_independent_of_target_outcome") is not True:
        raise ValueError("r12 prediction packet must use independent source")
    if gates.get("pre_outcome_revalidation_ready") is not False:
        raise ValueError("r12 prediction packet must not be pre-outcome ready")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 prediction packet must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 prediction packet must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 prediction packet must not allow Product default")


def _validate_independent_hindcast_revalidation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_independent_hindcast_revalidation.schema_version must be "
            f"{R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 independent hindcast acceptance_gates required")
    if gates.get("hindcast_independent_revalidation_executed") is not True:
        raise ValueError("r12 independent hindcast revalidation must execute")
    if gates.get("hindcast_independent_revalidation_passed") is not True:
        raise ValueError("r12 independent hindcast revalidation must pass")
    if gates.get("pre_outcome_revalidation_ready") is not False:
        raise ValueError("r12 independent hindcast must not be pre-outcome ready")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 independent hindcast must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 independent hindcast must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 independent hindcast must not allow Product default")


def _validate_pre_outcome_prediction_trial_or_customer_field_revalidation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_pre_outcome_prediction_trial_or_customer_field_revalidation."
            "schema_version must be "
            f"{R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 pre-outcome/customer field acceptance_gates required")
    if gates.get("pre_outcome_prediction_trial_created") is not True:
        raise ValueError("r12 pre-outcome prediction trial must be created")
    if gates.get("prediction_packet_locked") is not True:
        raise ValueError("r12 pre-outcome prediction packet must be locked")
    if gates.get("prediction_lock_timestamp_pre_target_outcome") is not True:
        raise ValueError("r12 prediction lock must be before target outcome")
    if gates.get("target_outcome_used_for_prediction_generation") is not False:
        raise ValueError("r12 pre-outcome trial must not use target outcome")
    if gates.get("pre_outcome_revalidation_ready") is not False:
        raise ValueError("r12 pre-outcome trial must not be revalidation-ready yet")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 pre-outcome trial must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 pre-outcome trial must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 pre-outcome trial must not allow Product default")


def _validate_pre_outcome_or_customer_field_outcome_ingestion(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_pre_outcome_or_customer_field_outcome_ingestion.schema_version "
            "must be "
            f"{R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 outcome ingestion acceptance_gates required")
    if gates.get("pre_outcome_trial_locked") is not True:
        raise ValueError("r12 outcome ingestion requires locked trial")
    if gates.get("target_outcome_artifact_present") is not False:
        raise ValueError("r12 outcome ingestion must not contain target outcome yet")
    if gates.get("field_or_pre_outcome_revalidation_ready") is not False:
        raise ValueError("r12 outcome ingestion must not be revalidation ready yet")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 outcome ingestion must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 outcome ingestion must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 outcome ingestion must not allow Product default")


def _validate_pre_outcome_or_customer_field_outcome_revalidation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_pre_outcome_or_customer_field_outcome_revalidation."
            "schema_version must be "
            f"{R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 outcome revalidation acceptance_gates required")
    if gates.get("pre_outcome_trial_locked") is not True:
        raise ValueError("r12 outcome revalidation requires locked trial")
    if gates.get("target_outcome_artifact_present") is not False:
        raise ValueError("r12 outcome revalidation must not contain target outcome")
    if gates.get("customer_field_slice_present") is not False:
        raise ValueError("r12 outcome revalidation must not contain field slice")
    if gates.get("field_or_pre_outcome_revalidation_ready") is not False:
        raise ValueError("r12 outcome revalidation must not be ready yet")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 outcome revalidation must not compute metrics yet")
    if gates.get("field_or_pre_outcome_revalidation_passed") is not False:
        raise ValueError("r12 outcome revalidation must not pass without outcome")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 outcome revalidation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 outcome revalidation must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 outcome revalidation must not allow Product default")


def _validate_target_outcome_or_customer_field_slice_arrival(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_target_outcome_or_customer_field_slice_arrival.schema_version "
            "must be "
            f"{R12_TARGET_OUTCOME_OR_CUSTOMER_FIELD_SLICE_ARRIVAL_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 target/customer slice arrival acceptance_gates required")
    if gates.get("revalidation_harness_ready") is not True:
        raise ValueError("r12 target/customer arrival requires revalidation harness")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 target/customer arrival must not compute metrics")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 target/customer arrival must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 target/customer arrival must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 target/customer arrival must not allow Product default")


def _validate_customer_field_slice_handoff_package(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_field_slice_handoff_package.schema_version must be "
            f"{R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 customer field slice handoff acceptance_gates required")
    if gates.get("customer_field_slice_template_generated") is not True:
        raise ValueError("r12 handoff must generate customer field slice template")
    if gates.get("customer_field_slice_contract_machine_checkable") is not True:
        raise ValueError("r12 handoff contract must be machine checkable")
    if gates.get("customer_data_request_ready") is not True:
        raise ValueError("r12 handoff customer data request must be ready")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 handoff must not compute metrics")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 handoff must not be field validated")
    if gates.get("direct_personal_identifiers_allowed") is not False:
        raise ValueError("r12 handoff must not allow direct personal identifiers")
    if gates.get("manual_prompt_or_persona_patch_allowed") is not False:
        raise ValueError("r12 handoff must not allow manual prompt/persona patch")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 handoff must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 handoff must not allow Product default")


def _validate_customer_field_slice_intake_validation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_field_slice_intake_validation.schema_version must be "
            f"{R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 customer field slice intake acceptance_gates required")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 customer field slice intake must not compute metrics")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 customer field slice intake must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 customer field slice intake must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 customer field slice intake must not allow Product default")


def _validate_customer_field_slice_revalidation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_field_slice_revalidation.schema_version must be "
            f"{R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 customer field slice revalidation acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer field slice revalidation must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer field slice revalidation must not allow runtime default"
        )


def _validate_customer_field_outcome_feedback_update(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_field_outcome_feedback_update.schema_version must be "
            f"{R12_CUSTOMER_FIELD_OUTCOME_FEEDBACK_UPDATE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer field outcome feedback update acceptance_gates required"
        )
    if gates.get("prompt_or_persona_manual_patch_allowed") is not False:
        raise ValueError(
            "r12 customer field outcome feedback update must not patch prompts "
            "or personas manually"
        )
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer field outcome feedback update must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer field outcome feedback update must not allow runtime default"
        )


def _validate_customer_feedback_update_shadow_replay(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_feedback_update_shadow_replay.schema_version must be "
            f"{R12_CUSTOMER_FEEDBACK_UPDATE_SHADOW_REPLAY_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer feedback update shadow replay acceptance_gates required"
        )
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer feedback shadow replay must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer feedback shadow replay must not allow runtime default"
        )


def _validate_customer_feedback_shadow_replay_holdout_review(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_feedback_shadow_replay_holdout_review.schema_version "
            "must be "
            f"{R12_CUSTOMER_FEEDBACK_SHADOW_REPLAY_HOLDOUT_REVIEW_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer feedback shadow replay holdout review "
            "acceptance_gates required"
        )
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer feedback holdout review must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer feedback holdout review must not allow runtime default"
        )


def _validate_customer_validation_workflow_status(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_validation_workflow_status.schema_version must be "
            f"{R12_CUSTOMER_VALIDATION_WORKFLOW_STATUS_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer validation workflow status acceptance_gates required"
        )
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer validation workflow must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer validation workflow must not allow runtime default"
        )


def _validate_customer_trial_readiness_package(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_trial_readiness_package.schema_version must be "
            f"{R12_CUSTOMER_TRIAL_READINESS_PACKAGE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer trial readiness package acceptance_gates required"
        )
    if gates.get("trial_readiness_package_ready") is not True:
        raise ValueError("r12 customer trial readiness package must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial readiness package must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial readiness package must not allow runtime default"
        )


def _validate_customer_trial_operational_check(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_trial_operational_check.schema_version must be "
            f"{R12_CUSTOMER_TRIAL_OPERATIONAL_CHECK_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer trial operational check acceptance_gates required"
        )
    if gates.get("trial_readiness_package_loaded") is not True:
        raise ValueError("r12 customer trial operational check must load L28 package")
    if gates.get("customer_trial_request_operationally_ready") is not True:
        raise ValueError("r12 customer trial operational check must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial operational check must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial operational check must not allow runtime default"
        )


def _validate_customer_trial_launch_handoff_package(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_trial_launch_handoff_package.schema_version must be "
            f"{R12_CUSTOMER_TRIAL_LAUNCH_HANDOFF_PACKAGE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer trial launch handoff package acceptance_gates required"
        )
    if gates.get("launch_handoff_package_ready") is not True:
        raise ValueError("r12 customer trial launch handoff package must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial launch handoff package must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial launch handoff package must not allow runtime default"
        )


def _validate_customer_trial_launch_packet_export(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_trial_launch_packet_export.schema_version must be "
            f"{R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer trial launch packet export acceptance_gates required"
        )
    if gates.get("launch_packet_export_ready") is not True:
        raise ValueError("r12 customer trial launch packet export must be ready")
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial launch packet export must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial launch packet export must not allow runtime default"
        )


def _validate_customer_trial_launch_bundle_verification(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_trial_launch_bundle_verification.schema_version must be "
            f"{R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer trial launch bundle verification acceptance_gates required"
        )
    if gates.get("launch_bundle_verified") is not True:
        raise ValueError("r12 customer trial launch bundle must be verified")
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial launch bundle must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer trial launch bundle must not allow runtime default"
        )


def _validate_customer_field_slice_operator_rehearsal(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_field_slice_operator_rehearsal.schema_version must be "
            f"{R12_CUSTOMER_FIELD_SLICE_OPERATOR_REHEARSAL_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer field slice operator rehearsal acceptance_gates required"
        )
    if gates.get("operator_command_rehearsed") is not True:
        raise ValueError("r12 customer field slice operator must be rehearsed")
    if gates.get("real_customer_field_slice_submitted") is not False:
        raise ValueError(
            "r12 customer field slice operator rehearsal must not claim real slice"
        )
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer field slice operator rehearsal must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer field slice operator rehearsal must not allow runtime default"
        )


def _validate_customer_feedback_loop_operator_rehearsal(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_feedback_loop_operator_rehearsal.schema_version must be "
            f"{R12_CUSTOMER_FEEDBACK_LOOP_OPERATOR_REHEARSAL_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError(
            "r12 customer feedback loop operator rehearsal acceptance_gates required"
        )
    required_true = [
        "l22_intake_validator_executed",
        "l23_field_revalidation_executed",
        "l24_feedback_candidates_generated",
        "l25_shadow_replay_executed",
        "l26_synthetic_holdout_review_executed",
    ]
    for gate in required_true:
        if gates.get(gate) is not True:
            raise ValueError(f"r12 customer feedback loop rehearsal must set {gate}")
    if gates.get("real_customer_field_slice_submitted") is not False:
        raise ValueError(
            "r12 customer feedback loop rehearsal must not claim real slice"
        )
    if gates.get("field_outcome_validated") is not False:
        raise ValueError(
            "r12 customer feedback loop rehearsal must not claim field validation"
        )
    if gates.get("product_default_allowed") is not False:
        raise ValueError(
            "r12 customer feedback loop rehearsal must not allow Product default"
        )
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError(
            "r12 customer feedback loop rehearsal must not allow runtime default"
        )


def _validate_customer_trial_evidence_ledger(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_customer_trial_evidence_ledger.schema_version must be "
            f"{R12_CUSTOMER_TRIAL_EVIDENCE_LEDGER_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 customer trial evidence ledger acceptance_gates required")
    if gates.get("customer_trial_evidence_ledger_ready") is not True:
        raise ValueError("r12 customer trial evidence ledger must be ready")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 customer trial evidence ledger must not claim field validation")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 customer trial evidence ledger must not allow Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 customer trial evidence ledger must not allow runtime default")


def _transfer_evidence_card(
    transfer_validation: dict[str, Any],
    *,
    positive_transfer: bool,
    high_risk_boundary: dict[str, Any] | None = None,
    high_risk_replay_boundary: dict[str, Any] | None = None,
    recall_update_boundary: dict[str, Any] | None = None,
    recall_false_alarm_stress_boundary: dict[str, Any] | None = None,
    recall_false_alarm_mitigation_boundary: dict[str, Any] | None = None,
    recall_mitigation_holdout_validation_boundary: dict[str, Any] | None = None,
    recall_mitigation_independent_holdout_data_boundary: dict[str, Any] | None = None,
    recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary: (
        dict[str, Any] | None
    ) = None,
    external_or_customer_holdout_raw_slice_boundary: dict[str, Any] | None = None,
    recall_mitigation_external_holdout_revalidation_boundary: (
        dict[str, Any] | None
    ) = None,
    pre_outcome_or_independent_prediction_packet_boundary: (
        dict[str, Any] | None
    ) = None,
    independent_hindcast_revalidation_boundary: dict[str, Any] | None = None,
    pre_outcome_prediction_trial_or_customer_field_revalidation_boundary: (
        dict[str, Any] | None
    ) = None,
    pre_outcome_or_customer_field_outcome_ingestion_boundary: (
        dict[str, Any] | None
    ) = None,
    pre_outcome_or_customer_field_outcome_revalidation_boundary: (
        dict[str, Any] | None
    ) = None,
    target_outcome_or_customer_field_slice_arrival_boundary: (
        dict[str, Any] | None
    ) = None,
    customer_field_slice_handoff_package_boundary: dict[str, Any] | None = None,
    customer_field_slice_intake_validation_boundary: dict[str, Any] | None = None,
    customer_field_slice_revalidation_boundary: dict[str, Any] | None = None,
    customer_field_outcome_feedback_update_boundary: (
        dict[str, Any] | None
    ) = None,
    customer_feedback_update_shadow_replay_boundary: (
        dict[str, Any] | None
    ) = None,
    customer_feedback_shadow_replay_holdout_review_boundary: (
        dict[str, Any] | None
    ) = None,
    customer_validation_workflow_status_boundary: dict[str, Any] | None = None,
    customer_trial_readiness_package_boundary: dict[str, Any] | None = None,
    customer_trial_operational_check_boundary: dict[str, Any] | None = None,
    customer_trial_launch_handoff_package_boundary: dict[str, Any] | None = None,
    customer_trial_launch_packet_export_boundary: dict[str, Any] | None = None,
    customer_trial_launch_bundle_verification_boundary: (
        dict[str, Any] | None
    ) = None,
    customer_field_slice_operator_rehearsal_boundary: (
        dict[str, Any] | None
    ) = None,
    customer_feedback_loop_operator_rehearsal_boundary: (
        dict[str, Any] | None
    ) = None,
    customer_trial_evidence_ledger_boundary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    split_metrics = transfer_validation["split_metrics"]
    validation = split_metrics["validation"]
    holdout = split_metrics["holdout"]
    evidence_summary = {
        "transfer_decision": transfer_validation["transfer_decision"],
        "accepted_update": transfer_validation["accepted_update"],
        "claim_level": transfer_validation["claim_level"],
        "train_metrics_used_for_transfer_decision": transfer_validation[
            "transfer_accounting"
        ]["train_metrics_used_for_transfer_decision"],
        "field_outcome_validated": transfer_validation["acceptance_gates"][
            "field_outcome_validated"
        ],
        "runtime_default_allowed": transfer_validation["acceptance_gates"][
            "runtime_default_allowed"
        ],
        "extended_metric_gates": transfer_validation["extended_metric_gates"],
    }
    if high_risk_boundary is not None:
        evidence_summary["high_risk_holdout_boundary"] = high_risk_boundary
    if high_risk_replay_boundary is not None:
        evidence_summary["high_risk_replay_boundary"] = high_risk_replay_boundary
    if recall_update_boundary is not None:
        evidence_summary["recall_oriented_update_boundary"] = recall_update_boundary
    if recall_false_alarm_stress_boundary is not None:
        evidence_summary["recall_false_alarm_stress_boundary"] = (
            recall_false_alarm_stress_boundary
        )
    if recall_false_alarm_mitigation_boundary is not None:
        evidence_summary["recall_false_alarm_mitigation_boundary"] = (
            recall_false_alarm_mitigation_boundary
        )
    if recall_mitigation_holdout_validation_boundary is not None:
        evidence_summary["recall_mitigation_holdout_validation_boundary"] = (
            recall_mitigation_holdout_validation_boundary
        )
    if recall_mitigation_independent_holdout_data_boundary is not None:
        evidence_summary[
            "recall_mitigation_independent_holdout_data_boundary"
        ] = recall_mitigation_independent_holdout_data_boundary
    if (
        recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary
        is not None
    ):
        evidence_summary[
            "recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary"
        ] = recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary
    if external_or_customer_holdout_raw_slice_boundary is not None:
        evidence_summary[
            "external_or_customer_holdout_raw_slice_boundary"
        ] = external_or_customer_holdout_raw_slice_boundary
    if recall_mitigation_external_holdout_revalidation_boundary is not None:
        evidence_summary[
            "recall_mitigation_external_holdout_revalidation_boundary"
        ] = recall_mitigation_external_holdout_revalidation_boundary
    if pre_outcome_or_independent_prediction_packet_boundary is not None:
        evidence_summary[
            "pre_outcome_or_independent_prediction_packet_boundary"
        ] = pre_outcome_or_independent_prediction_packet_boundary
    if independent_hindcast_revalidation_boundary is not None:
        evidence_summary[
            "independent_hindcast_revalidation_boundary"
        ] = independent_hindcast_revalidation_boundary
    if (
        pre_outcome_prediction_trial_or_customer_field_revalidation_boundary
        is not None
    ):
        evidence_summary[
            "pre_outcome_prediction_trial_or_customer_field_revalidation_boundary"
        ] = pre_outcome_prediction_trial_or_customer_field_revalidation_boundary
    if pre_outcome_or_customer_field_outcome_ingestion_boundary is not None:
        evidence_summary[
            "pre_outcome_or_customer_field_outcome_ingestion_boundary"
        ] = pre_outcome_or_customer_field_outcome_ingestion_boundary
    if pre_outcome_or_customer_field_outcome_revalidation_boundary is not None:
        evidence_summary[
            "pre_outcome_or_customer_field_outcome_revalidation_boundary"
        ] = pre_outcome_or_customer_field_outcome_revalidation_boundary
    if target_outcome_or_customer_field_slice_arrival_boundary is not None:
        evidence_summary[
            "target_outcome_or_customer_field_slice_arrival_boundary"
        ] = target_outcome_or_customer_field_slice_arrival_boundary
    if customer_field_slice_handoff_package_boundary is not None:
        evidence_summary[
            "customer_field_slice_handoff_package_boundary"
        ] = customer_field_slice_handoff_package_boundary
    if customer_field_slice_intake_validation_boundary is not None:
        evidence_summary[
            "customer_field_slice_intake_validation_boundary"
        ] = customer_field_slice_intake_validation_boundary
    if customer_field_slice_revalidation_boundary is not None:
        evidence_summary[
            "customer_field_slice_revalidation_boundary"
        ] = customer_field_slice_revalidation_boundary
    if customer_field_outcome_feedback_update_boundary is not None:
        evidence_summary[
            "customer_field_outcome_feedback_update_boundary"
        ] = customer_field_outcome_feedback_update_boundary
    if customer_feedback_update_shadow_replay_boundary is not None:
        evidence_summary[
            "customer_feedback_update_shadow_replay_boundary"
        ] = customer_feedback_update_shadow_replay_boundary
    if customer_feedback_shadow_replay_holdout_review_boundary is not None:
        evidence_summary[
            "customer_feedback_shadow_replay_holdout_review_boundary"
        ] = customer_feedback_shadow_replay_holdout_review_boundary
    if customer_validation_workflow_status_boundary is not None:
        evidence_summary[
            "customer_validation_workflow_status_boundary"
        ] = customer_validation_workflow_status_boundary
    if customer_trial_readiness_package_boundary is not None:
        evidence_summary[
            "customer_trial_readiness_package_boundary"
        ] = customer_trial_readiness_package_boundary
    if customer_trial_operational_check_boundary is not None:
        evidence_summary[
            "customer_trial_operational_check_boundary"
        ] = customer_trial_operational_check_boundary
    if customer_trial_launch_handoff_package_boundary is not None:
        evidence_summary[
            "customer_trial_launch_handoff_package_boundary"
        ] = customer_trial_launch_handoff_package_boundary
    if customer_trial_launch_packet_export_boundary is not None:
        evidence_summary[
            "customer_trial_launch_packet_export_boundary"
        ] = customer_trial_launch_packet_export_boundary
    if customer_trial_launch_bundle_verification_boundary is not None:
        evidence_summary[
            "customer_trial_launch_bundle_verification_boundary"
        ] = customer_trial_launch_bundle_verification_boundary
    if customer_field_slice_operator_rehearsal_boundary is not None:
        evidence_summary[
            "customer_field_slice_operator_rehearsal_boundary"
        ] = customer_field_slice_operator_rehearsal_boundary
    if customer_feedback_loop_operator_rehearsal_boundary is not None:
        evidence_summary[
            "customer_feedback_loop_operator_rehearsal_boundary"
        ] = customer_feedback_loop_operator_rehearsal_boundary
    if customer_trial_evidence_ledger_boundary is not None:
        evidence_summary[
            "customer_trial_evidence_ledger_boundary"
        ] = customer_trial_evidence_ledger_boundary
    return {
        "card_id": "r12_transfer_validation_evidence_card",
        "title": "R12 guarded transfer validation evidence",
        "claim_status": (
            "guarded_transfer_positive_secondary_evidence"
            if positive_transfer
            else "guarded_transfer_blocked_or_diagnostic"
        ),
        "display_allowed": True,
        "primary_decision_allowed": False,
        "metrics": {
            "update_transfer_gain": transfer_validation["update_transfer_gain"],
            "validation_mean_absolute_error_delta": validation[
                "mean_absolute_error_delta"
            ],
            "holdout_mean_absolute_error_delta": holdout[
                "mean_absolute_error_delta"
            ],
            "interval_coverage_delta": holdout["interval_coverage_delta"],
            "false_alarm_rate_delta": holdout["false_alarm_rate_delta"],
        },
        "evidence_summary": evidence_summary,
        "allowed_display_claims": [
            (
                "R12 has a guarded public-proxy transfer signal that can be "
                "shown as secondary evidence."
            ),
            (
                "R12 evidence remains runtime-off and requires field or "
                "customer outcome review before any default update."
            ),
        ],
        "blocked_display_claims": [
            "R12 primary decision",
            "R12 field validated",
            "R12 runtime default",
            "R12 precise point prediction",
            "R12 Product core method ready",
        ],
        "source_artifact_ids": [transfer_validation["artifact_id"]],
    }


def _high_risk_holdout_boundary(
    registry: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if registry is None:
        return None
    summary = registry["candidate_summary"]
    gates = registry["acceptance_gates"]
    return {
        "registry_status": registry["status"],
        "research_eligible_case_count": summary["research_eligible_case_count"],
        "research_recoverable_static_prior_miss_count": summary[
            "research_recoverable_static_prior_miss_count"
        ],
        "product_default_eligible_case_count": summary[
            "product_default_eligible_case_count"
        ],
        "product_default_low_sensitive_high_risk_holdout_present": gates[
            "product_default_low_sensitive_high_risk_holdout_present"
        ],
        "product_claim_boundary": (
            "research_only_until_low_sensitive_or_customer_approved_holdout"
        ),
    }


def _high_risk_replay_boundary(
    replay: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if replay is None:
        return None
    metrics = replay["metric_comparison"]
    gates = replay["acceptance_gates"]
    return {
        "replay_status": replay["status"],
        "transfer_decision": replay["transfer_decision"],
        "mean_absolute_error_delta": metrics["mean_absolute_error"]["delta"],
        "static_prior_miss_recovery_delta": metrics[
            "static_prior_miss_recovery"
        ]["delta"],
        "abnormal_segment_recall_delta": metrics["abnormal_segment_recall"][
            "delta"
        ],
        "product_support_level": replay["product_support_level"],
        "product_default_eligible_high_risk_holdout_present": gates[
            "product_default_eligible_high_risk_holdout_present"
        ],
    }


def _recall_oriented_update_boundary(
    recall_update: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if recall_update is None:
        return None
    metrics = recall_update["metric_comparison"]
    update_candidate = recall_update["update_candidate"]
    return {
        "update_status": recall_update["status"],
        "acceptance_decision": recall_update["acceptance_decision"],
        "recommended_activation_margin": update_candidate["recommended_value"],
        "static_prior_miss_recovery_delta": metrics[
            "static_prior_miss_recovery"
        ]["delta"],
        "abnormal_segment_recall_delta": metrics["abnormal_segment_recall"][
            "delta"
        ],
        "false_alarm_rate_delta": metrics["false_alarm_rate"]["delta"],
        "precision_delta": metrics["precision"]["delta"],
        "product_default_allowed": update_candidate["product_default_allowed"],
        "next_required_artifact": recall_update["next_required_artifact"],
    }


def _recall_false_alarm_stress_boundary(
    stress: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if stress is None:
        return None
    global_tradeoff = stress["stress_metrics"]["global_tradeoff"]
    low_sensitive = stress["stress_metrics"]["low_sensitive_false_alarm"]
    protected_sensitive = stress["stress_metrics"][
        "protected_sensitive_false_alarm"
    ]
    concentration = stress["stress_metrics"]["false_alarm_concentration"]
    return {
        "stress_status": stress["status"],
        "acceptance_decision": stress["acceptance_decision"],
        "global_recall_delta": global_tradeoff["recall_delta"],
        "global_false_alarm_rate_delta": global_tradeoff[
            "false_alarm_rate_delta"
        ],
        "precision_delta": global_tradeoff["precision_delta"],
        "low_sensitive_recall_evaluable": low_sensitive["recall_evaluable"],
        "low_sensitive_false_alarm_rate_delta": low_sensitive[
            "false_alarm_rate_delta"
        ],
        "protected_sensitive_false_alarm_rate_delta": protected_sensitive[
            "false_alarm_rate_delta"
        ],
        "dominant_false_alarm_segment_column": concentration[
            "dominant_segment_column"
        ],
        "product_default_allowed": stress["acceptance_gates"][
            "product_default_allowed"
        ],
        "next_required_artifact": stress["next_required_artifact"],
    }


def _recall_false_alarm_mitigation_boundary(
    mitigation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if mitigation is None:
        return None
    selected = mitigation["selected_candidate"]
    metrics = mitigation["metric_comparison"]
    return {
        "mitigation_status": mitigation["status"],
        "acceptance_decision": mitigation["acceptance_decision"],
        "candidate_id": selected["candidate_id"],
        "target_segment_column": selected["target_segment_column"],
        "target_segment_value_min": selected["target_segment_value_min"],
        "target_segment_value_max": selected["target_segment_value_max"],
        "mitigated_recall_delta": metrics["static_prior_miss_recovery"][
            "mitigated_delta"
        ],
        "l7_recall_gain_retained": metrics["static_prior_miss_recovery"][
            "l7_recall_gain_retained"
        ],
        "mitigated_false_alarm_rate_delta": metrics["false_alarm_rate"][
            "mitigated_delta"
        ],
        "mitigated_precision_delta": metrics["precision"]["mitigated_delta"],
        "overfit_risk": selected["overfit_risk"],
        "product_default_allowed": selected["product_default_allowed"],
        "next_required_artifact": mitigation["next_required_artifact"],
    }


def _recall_mitigation_holdout_validation_boundary(
    validation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if validation is None:
        return None
    leave_one = validation["leave_one_false_alarm_band_validation"]
    gates = validation["acceptance_gates"]
    stable_alternative = validation["stable_alternative_check"]
    return {
        "validation_status": validation["status"],
        "acceptance_decision": validation["acceptance_decision"],
        "leave_one_pass_rate": leave_one["pass_rate"],
        "endpoint_holdout_failure_count": leave_one[
            "endpoint_holdout_failure_count"
        ],
        "independent_holdout_present": gates["independent_holdout_present"],
        "low_sensitive_recall_evaluable": gates[
            "low_sensitive_recall_evaluable"
        ],
        "stable_alternative_recall_retained": stable_alternative[
            "l7_recall_gain_retained"
        ],
        "mitigation_holdout_validated": gates["mitigation_holdout_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": validation["next_required_artifact"],
    }


def _recall_mitigation_independent_holdout_data_boundary(
    data_audit: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if data_audit is None:
        return None
    summary = data_audit["data_summary"]
    gates = data_audit["acceptance_gates"]
    return {
        "data_status": data_audit["status"],
        "acceptance_decision": data_audit["acceptance_decision"],
        "same_dataset_non_derivation_recall_candidate_count": summary[
            "same_dataset_non_derivation_recall_candidate_count"
        ],
        "low_sensitive_observed_high_risk_count": summary[
            "low_sensitive_observed_high_risk_count"
        ],
        "external_registry_candidate_count": summary[
            "external_registry_candidate_count"
        ],
        "ingested_external_independent_dataset_count": summary[
            "ingested_external_independent_dataset_count"
        ],
        "mitigation_independent_data_ready": gates[
            "mitigation_independent_data_ready"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": data_audit["next_required_artifact"],
    }


def _recall_mitigation_external_holdout_ingestion_or_customer_slice_boundary(
    contract: dict[str, Any] | None,
    *,
    r12_external_or_customer_holdout_raw_slice: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if contract is None:
        return None
    route = contract["route_selection"]
    gates = contract["acceptance_gates"]
    raw_slice_gates = (
        r12_external_or_customer_holdout_raw_slice or {}
    ).get("acceptance_gates", {})
    return {
        "contract_status": contract["status"],
        "selected_route": route["selected_route"],
        "preferred_external_source_id": route["preferred_external_source_id"],
        "customer_slice_fallback_enabled": route[
            "customer_slice_fallback_enabled"
        ],
        "raw_external_or_customer_slice_present": raw_slice_gates.get(
            "raw_external_or_customer_slice_present",
            gates["raw_external_or_customer_slice_present"],
        ),
        "minimum_case_count_met": raw_slice_gates.get(
            "minimum_case_count_met",
            gates["minimum_case_count_met"],
        ),
        "customer_approval_present": gates["customer_approval_present"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": (
            r12_external_or_customer_holdout_raw_slice or contract
        )["next_required_artifact"],
    }


def _external_or_customer_holdout_raw_slice_boundary(
    raw_slice: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if raw_slice is None:
        return None
    gates = raw_slice["acceptance_gates"]
    summary = raw_slice["raw_slice_summary"]
    selection = raw_slice["slice_selection"]
    return {
        "raw_slice_status": raw_slice["status"],
        "selected_source_id": selection["selected_source_id"],
        "case_count": summary["case_count"],
        "source_row_count": summary["source_row_count"],
        "total_observed_complaint_cases": summary[
            "total_observed_complaint_cases"
        ],
        "actual_public_data_ingested": gates["actual_public_data_ingested"],
        "prediction_fields_present": gates["prediction_fields_present"],
        "external_holdout_revalidation_ready": gates[
            "external_holdout_revalidation_ready"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": raw_slice["next_required_artifact"],
    }


def _recall_mitigation_external_holdout_revalidation_boundary(
    revalidation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if revalidation is None:
        return None
    metrics = revalidation["metric_comparison"]
    gates = revalidation["acceptance_gates"]
    summary = revalidation["revalidation_summary"]
    return {
        "revalidation_status": revalidation["status"],
        "acceptance_decision": revalidation["acceptance_decision"],
        "case_count": summary["case_count"],
        "mean_absolute_error_delta": metrics["mean_absolute_error"]["delta"],
        "interval_coverage_delta": metrics["interval_coverage"]["delta"],
        "risk_ranking_quality_delta": metrics["risk_ranking_quality"]["delta"],
        "static_prior_miss_recovery_delta": metrics[
            "static_prior_miss_recovery"
        ]["delta"],
        "false_alarm_rate_delta": metrics["false_alarm_rate"]["delta"],
        "prediction_source_independent_of_observed_outcome": gates[
            "prediction_source_independent_of_observed_outcome"
        ],
        "same_table_prediction_leakage_risk": gates[
            "same_table_prediction_leakage_risk"
        ],
        "external_holdout_revalidation_passed": gates[
            "external_holdout_revalidation_passed"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": revalidation["next_required_artifact"],
    }


def _pre_outcome_or_independent_prediction_packet_boundary(
    packet: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if packet is None:
        return None
    summary = packet["prediction_packet_summary"]
    gates = packet["acceptance_gates"]
    contract = packet["prediction_generation_contract"]
    return {
        "packet_status": packet["status"],
        "acceptance_decision": packet["acceptance_decision"],
        "prediction_route": contract["prediction_route"],
        "prediction_case_count": summary["prediction_case_count"],
        "matched_case_count": summary["matched_case_count"],
        "prediction_source_independent_of_target_outcome": gates[
            "prediction_source_independent_of_target_outcome"
        ],
        "prediction_lock_timestamp_pre_target_outcome": gates[
            "prediction_lock_timestamp_pre_target_outcome"
        ],
        "same_table_prediction_leakage_risk": gates[
            "same_table_prediction_leakage_risk"
        ],
        "hindcast_independent_revalidation_ready": gates[
            "hindcast_independent_revalidation_ready"
        ],
        "pre_outcome_revalidation_ready": gates[
            "pre_outcome_revalidation_ready"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": packet["next_required_artifact"],
    }


def _independent_hindcast_revalidation_boundary(
    hindcast: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if hindcast is None:
        return None
    metrics = hindcast["metric_comparison"]
    gates = hindcast["acceptance_gates"]
    summary = hindcast["hindcast_summary"]
    return {
        "hindcast_status": hindcast["status"],
        "acceptance_decision": hindcast["acceptance_decision"],
        "case_count": summary["case_count"],
        "mean_absolute_error_delta": metrics["mean_absolute_error"]["delta"],
        "interval_coverage_delta": metrics["interval_coverage"]["delta"],
        "risk_ranking_quality_delta": metrics["risk_ranking_quality"]["delta"],
        "static_prior_miss_recovery_delta": metrics[
            "static_prior_miss_recovery"
        ]["delta"],
        "false_alarm_rate_delta": metrics["false_alarm_rate"]["delta"],
        "decision_value_delta": metrics["decision_value"]["delta"],
        "prediction_source_independent_of_target_outcome": gates[
            "prediction_source_independent_of_target_outcome"
        ],
        "prediction_lock_timestamp_pre_target_outcome": gates[
            "prediction_lock_timestamp_pre_target_outcome"
        ],
        "hindcast_independent_revalidation_passed": gates[
            "hindcast_independent_revalidation_passed"
        ],
        "pre_outcome_revalidation_ready": gates[
            "pre_outcome_revalidation_ready"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": hindcast["next_required_artifact"],
    }


def _pre_outcome_prediction_trial_or_customer_field_revalidation_boundary(
    trial: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if trial is None:
        return None
    summary = trial["trial_summary"]
    route = trial["route_selection"]
    gates = trial["acceptance_gates"]
    return {
        "trial_status": trial["status"],
        "acceptance_decision": trial["acceptance_decision"],
        "selected_route": route["selected_route"],
        "prediction_lock_timestamp": summary["prediction_lock_timestamp"],
        "feature_period": summary["feature_period"],
        "target_outcome_period": summary["target_outcome_period"],
        "prediction_case_count": summary["prediction_case_count"],
        "prediction_lock_timestamp_pre_target_outcome": gates[
            "prediction_lock_timestamp_pre_target_outcome"
        ],
        "target_outcome_artifact_present": gates[
            "target_outcome_artifact_present"
        ],
        "pre_outcome_revalidation_ready": gates[
            "pre_outcome_revalidation_ready"
        ],
        "customer_field_slice_contract_ready": gates[
            "customer_field_slice_contract_ready"
        ],
        "customer_field_slice_present": gates["customer_field_slice_present"],
        "customer_approval_present": gates["customer_approval_present"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": trial["next_required_artifact"],
    }


def _pre_outcome_or_customer_field_outcome_ingestion_boundary(
    ingestion: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if ingestion is None:
        return None
    summary = ingestion["ingestion_summary"]
    availability = ingestion["public_source_availability"]
    gates = ingestion["acceptance_gates"]
    return {
        "ingestion_status": ingestion["status"],
        "acceptance_decision": ingestion["acceptance_decision"],
        "target_outcome_period": summary["target_outcome_period"],
        "availability_checked_at": summary["availability_checked_at"],
        "latest_available_report": availability["latest_available_report"],
        "target_public_outcome_available": gates[
            "target_public_outcome_available"
        ],
        "target_outcome_artifact_present": gates[
            "target_outcome_artifact_present"
        ],
        "customer_field_slice_contract_ready": gates[
            "customer_field_slice_contract_ready"
        ],
        "customer_field_slice_present": gates["customer_field_slice_present"],
        "field_or_pre_outcome_revalidation_ready": gates[
            "field_or_pre_outcome_revalidation_ready"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": ingestion["next_required_artifact"],
    }


def _pre_outcome_or_customer_field_outcome_revalidation_boundary(
    revalidation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if revalidation is None:
        return None
    summary = revalidation["revalidation_summary"]
    gates = revalidation["acceptance_gates"]
    return {
        "revalidation_status": revalidation["status"],
        "acceptance_decision": revalidation["acceptance_decision"],
        "target_outcome_period": summary["target_outcome_period"],
        "metrics_computed": gates["metrics_computed"],
        "field_or_pre_outcome_revalidation_ready": gates[
            "field_or_pre_outcome_revalidation_ready"
        ],
        "field_or_pre_outcome_revalidation_passed": gates[
            "field_or_pre_outcome_revalidation_passed"
        ],
        "target_outcome_artifact_present": gates[
            "target_outcome_artifact_present"
        ],
        "customer_field_slice_present": gates["customer_field_slice_present"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": revalidation["next_required_artifact"],
    }


def _target_outcome_or_customer_field_slice_arrival_boundary(
    arrival: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if arrival is None:
        return None
    summary = arrival["arrival_summary"]
    gates = arrival["acceptance_gates"]
    return {
        "arrival_status": arrival["status"],
        "acceptance_decision": arrival["acceptance_decision"],
        "target_outcome_period": summary["target_outcome_period"],
        "outcome_source_arrived": gates["outcome_source_arrived"],
        "target_outcome_artifact_present": gates[
            "target_outcome_artifact_present"
        ],
        "customer_field_slice_present": gates["customer_field_slice_present"],
        "customer_approval_present": gates["customer_approval_present"],
        "field_or_pre_outcome_revalidation_ready": gates[
            "field_or_pre_outcome_revalidation_ready"
        ],
        "metrics_computed": gates["metrics_computed"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": arrival["next_required_artifact"],
    }


def _customer_field_slice_handoff_package_boundary(
    handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if handoff is None:
        return None
    summary = handoff["handoff_summary"]
    gates = handoff["acceptance_gates"]
    return {
        "handoff_status": handoff["status"],
        "acceptance_decision": handoff["acceptance_decision"],
        "target_outcome_period": summary["target_outcome_period"],
        "minimum_case_count": summary["minimum_case_count"],
        "template_output_path": summary["template_output_path"],
        "customer_data_request_ready": gates["customer_data_request_ready"],
        "customer_field_slice_contract_machine_checkable": gates[
            "customer_field_slice_contract_machine_checkable"
        ],
        "metrics_computed": gates["metrics_computed"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": handoff["next_required_artifact"],
    }


def _customer_field_slice_intake_validation_boundary(
    intake: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if intake is None:
        return None
    summary = intake["intake_summary"]
    gates = intake["acceptance_gates"]
    return {
        "intake_status": intake["status"],
        "acceptance_decision": intake["acceptance_decision"],
        "case_count": summary["case_count"],
        "minimum_case_count": summary["minimum_case_count"],
        "ready_for_revalidation": gates["ready_for_revalidation"],
        "privacy_valid": gates["privacy_valid"],
        "numeric_fields_valid": gates["numeric_fields_valid"],
        "timestamps_valid": gates["timestamps_valid"],
        "duplicate_case_ids_absent": gates["duplicate_case_ids_absent"],
        "metrics_computed": gates["metrics_computed"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": intake["next_required_artifact"],
    }


def _customer_field_slice_revalidation_boundary(
    revalidation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if revalidation is None:
        return None
    summary = revalidation["revalidation_summary"]
    gates = revalidation["acceptance_gates"]
    metrics = revalidation["metric_results"]
    return {
        "revalidation_status": revalidation["status"],
        "acceptance_decision": revalidation["acceptance_decision"],
        "case_count": summary["case_count"],
        "metrics_computed": gates["metrics_computed"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "mean_absolute_error": metrics.get("mean_absolute_error"),
        "risk_ranking_quality": metrics.get("risk_ranking_quality"),
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": revalidation["next_required_artifact"],
    }


def _customer_field_outcome_feedback_update_boundary(
    feedback: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if feedback is None:
        return None
    summary = feedback["feedback_summary"]
    gates = feedback["acceptance_gates"]
    return {
        "feedback_update_status": feedback["status"],
        "acceptance_decision": feedback["acceptance_decision"],
        "metrics_consumed": gates["metrics_consumed"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "candidate_count": summary["candidate_count"],
        "prompt_or_persona_manual_patch_allowed": gates[
            "prompt_or_persona_manual_patch_allowed"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": feedback["next_required_artifact"],
    }


def _customer_feedback_update_shadow_replay_boundary(
    replay: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if replay is None:
        return None
    summary = replay["shadow_replay_summary"]
    gates = replay["acceptance_gates"]
    return {
        "shadow_replay_status": replay["status"],
        "acceptance_decision": replay["acceptance_decision"],
        "candidate_count": summary["candidate_count"],
        "replay_executed": gates["shadow_replay_executed"],
        "accepted_candidate_count": summary["accepted_candidate_count"],
        "at_least_one_candidate_passed": gates["at_least_one_candidate_passed"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": replay["next_required_artifact"],
    }


def _customer_feedback_shadow_replay_holdout_review_boundary(
    review: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if review is None:
        return None
    summary = review["holdout_review_summary"]
    gates = review["acceptance_gates"]
    return {
        "holdout_review_status": review["status"],
        "acceptance_decision": review["acceptance_decision"],
        "accepted_shadow_candidate_count": summary[
            "accepted_shadow_candidate_count"
        ],
        "independent_holdout_case_count": summary[
            "independent_holdout_case_count"
        ],
        "holdout_review_executed": gates["holdout_review_executed"],
        "holdout_review_passed": gates["holdout_review_passed"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": review["next_required_artifact"],
    }


def _customer_validation_workflow_status_boundary(
    workflow: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if workflow is None:
        return None
    summary = workflow["workflow_summary"]
    gates = workflow["acceptance_gates"]
    return {
        "workflow_status": workflow["status"],
        "current_stage": summary["current_stage"],
        "next_action": summary["next_action"],
        "blocking_artifact_id": summary["blocking_artifact_id"],
        "source_arrived": summary["source_arrived"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "feedback_candidate_count": summary["feedback_candidate_count"],
        "shadow_replay_executed": gates["shadow_replay_executed"],
        "holdout_review_executed": gates["holdout_review_executed"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": workflow["next_required_artifact"],
    }


def _customer_trial_readiness_package_boundary(
    package: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if package is None:
        return None
    summary = package["trial_readiness_summary"]
    gates = package["acceptance_gates"]
    return {
        "trial_package_status": package["status"],
        "current_stage": summary["current_stage"],
        "next_action": summary["next_action"],
        "customer_data_request_ready": gates["customer_data_request_ready"],
        "template_output_path": summary["template_output_path"],
        "minimum_case_count": summary["minimum_case_count"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": package["next_required_artifact"],
    }


def _customer_trial_operational_check_boundary(
    operational_check: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if operational_check is None:
        return None
    summary = operational_check["operational_summary"]
    gates = operational_check["acceptance_gates"]
    return {
        "operational_check_status": operational_check["status"],
        "current_stage": summary["current_stage"],
        "next_action": summary["next_action"],
        "customer_trial_request_operationally_ready": gates[
            "customer_trial_request_operationally_ready"
        ],
        "template_path_resolvable": gates["template_path_resolvable"],
        "template_required_fields_present": gates[
            "template_required_fields_present"
        ],
        "source_registry_resolvable": gates["source_registry_resolvable"],
        "operator_runbook_declared": gates["operator_runbook_declared"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": operational_check["next_required_artifact"],
    }


def _customer_trial_launch_handoff_package_boundary(
    package: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if package is None:
        return None
    summary = package["launch_summary"]
    gates = package["acceptance_gates"]
    return {
        "launch_package_status": package["status"],
        "current_stage": summary["current_stage"],
        "next_action": summary["next_action"],
        "launch_handoff_ready": gates["launch_handoff_package_ready"],
        "template_path": summary["template_path"],
        "minimum_case_count": summary["minimum_case_count"],
        "required_field_count": summary["required_field_count"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": package["next_required_artifact"],
    }


def _customer_trial_launch_packet_export_boundary(
    export: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if export is None:
        return None
    summary = export["export_summary"]
    gates = export["acceptance_gates"]
    return {
        "packet_export_status": export["status"],
        "current_stage": summary["current_stage"],
        "launch_handoff_ready": summary["launch_handoff_ready"],
        "markdown_export_written": gates["markdown_export_written"],
        "markdown_output_path": summary["markdown_output_path"],
        "customer_field_slice_present": gates["customer_field_slice_present"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": export["next_required_artifact"],
    }


def _customer_trial_launch_bundle_verification_boundary(
    verification: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if verification is None:
        return None
    summary = verification["bundle_summary"]
    gates = verification["acceptance_gates"]
    return {
        "bundle_verification_status": verification["status"],
        "current_stage": summary["current_stage"],
        "launch_bundle_verified": gates["launch_bundle_verified"],
        "required_item_count": summary["required_item_count"],
        "resolved_required_item_count": summary["resolved_required_item_count"],
        "missing_required_item_ids": summary["missing_required_item_ids"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": verification["next_required_artifact"],
    }


def _customer_field_slice_operator_rehearsal_boundary(
    rehearsal: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if rehearsal is None:
        return None
    summary = rehearsal["rehearsal_summary"]
    gates = rehearsal["acceptance_gates"]
    return {
        "operator_rehearsal_status": rehearsal["status"],
        "sample_slice_kind": summary["sample_slice_kind"],
        "operator_command_rehearsed": gates["operator_command_rehearsed"],
        "sample_slice_ready_for_revalidation": summary[
            "sample_slice_ready_for_revalidation"
        ],
        "real_customer_field_slice_submitted": gates[
            "real_customer_field_slice_submitted"
        ],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": rehearsal["next_required_artifact"],
    }


def _customer_feedback_loop_operator_rehearsal_boundary(
    rehearsal: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if rehearsal is None:
        return None
    summary = rehearsal["rehearsal_summary"]
    gates = rehearsal["acceptance_gates"]
    return {
        "feedback_loop_rehearsal_status": rehearsal["status"],
        "sample_slice_kind": summary["sample_slice_kind"],
        "l22_intake_validator_executed": gates["l22_intake_validator_executed"],
        "l23_field_revalidation_executed": gates[
            "l23_field_revalidation_executed"
        ],
        "l24_feedback_candidates_generated": gates[
            "l24_feedback_candidates_generated"
        ],
        "l25_shadow_replay_executed": gates["l25_shadow_replay_executed"],
        "l26_synthetic_holdout_review_executed": gates[
            "l26_synthetic_holdout_review_executed"
        ],
        "real_customer_field_slice_submitted": gates[
            "real_customer_field_slice_submitted"
        ],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": rehearsal["next_required_artifact"],
    }


def _customer_trial_evidence_ledger_boundary(
    ledger: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if ledger is None:
        return None
    summary = ledger["ledger_summary"]
    gates = ledger["acceptance_gates"]
    return {
        "ledger_status": ledger["status"],
        "launch_bundle_verified": summary["launch_bundle_verified"],
        "operator_rehearsal_executed": summary["operator_rehearsal_executed"],
        "feedback_loop_rehearsed_l22_to_l26": summary[
            "feedback_loop_rehearsed_l22_to_l26"
        ],
        "customer_visible_readiness_evidence_count": summary[
            "customer_visible_readiness_evidence_count"
        ],
        "operator_only_rehearsal_evidence_count": summary[
            "operator_only_rehearsal_evidence_count"
        ],
        "blocking_gap_count": summary["blocking_gap_count"],
        "field_outcome_validated": gates["field_outcome_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": ledger["next_required_artifact"],
    }


def _public_data_validation_scope(
    *,
    r12_external_or_customer_holdout_raw_slice: dict[str, Any] | None,
    r12_pre_outcome_or_independent_prediction_packet: dict[str, Any] | None,
    r12_independent_hindcast_revalidation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if r12_independent_hindcast_revalidation is None:
        return None
    gates = r12_independent_hindcast_revalidation["acceptance_gates"]
    has_required_public_evidence = (
        r12_external_or_customer_holdout_raw_slice is not None
        and r12_pre_outcome_or_independent_prediction_packet is not None
    )
    claim_allowed = (
        has_required_public_evidence
        and gates["hindcast_independent_revalidation_passed"] is True
        and gates["false_alarm_non_regression"] is True
    )
    return {
        "stage": "public_data_validation_only",
        "public_data_effectiveness_claim_allowed": claim_allowed,
        "public_data_effectiveness_claim": (
            "tested_effective_on_public_data_guarded"
            if claim_allowed
            else "public_data_effectiveness_not_established"
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
        "validated_public_metrics": (
            [
                "mean_absolute_error_delta",
                "interval_coverage_delta",
                "risk_ranking_quality_delta",
                "static_prior_miss_recovery_delta",
                "false_alarm_rate_delta",
                "decision_value_delta",
            ]
            if claim_allowed
            else []
        ),
    }


def _source_registry(
    *,
    r12_transfer_validation: dict[str, Any],
    r12_high_risk_holdout_registry: dict[str, Any] | None,
    r12_high_risk_holdout_transfer_replay: dict[str, Any] | None,
    r12_recall_oriented_update: dict[str, Any] | None,
    r12_recall_update_false_alarm_stress_test: dict[str, Any] | None,
    r12_recall_false_alarm_mitigation_candidate: dict[str, Any] | None,
    r12_recall_mitigation_holdout_validation: dict[str, Any] | None,
    r12_recall_mitigation_independent_holdout_data: dict[str, Any] | None,
    r12_recall_mitigation_external_holdout_ingestion_or_customer_slice: (
        dict[str, Any] | None
    ),
    r12_external_or_customer_holdout_raw_slice: dict[str, Any] | None,
    r12_recall_mitigation_external_holdout_revalidation: dict[str, Any] | None,
    r12_pre_outcome_or_independent_prediction_packet: dict[str, Any] | None,
    r12_independent_hindcast_revalidation: dict[str, Any] | None,
    r12_pre_outcome_prediction_trial_or_customer_field_revalidation: (
        dict[str, Any] | None
    ),
    r12_pre_outcome_or_customer_field_outcome_ingestion: dict[str, Any] | None,
    r12_pre_outcome_or_customer_field_outcome_revalidation: (
        dict[str, Any] | None
    ),
    r12_target_outcome_or_customer_field_slice_arrival: (
        dict[str, Any] | None
    ),
    r12_customer_field_slice_handoff_package: dict[str, Any] | None,
    r12_customer_field_slice_intake_validation: dict[str, Any] | None,
    r12_customer_field_slice_revalidation: dict[str, Any] | None,
    r12_customer_field_outcome_feedback_update: dict[str, Any] | None,
    r12_customer_feedback_update_shadow_replay: dict[str, Any] | None,
    r12_customer_feedback_shadow_replay_holdout_review: (
        dict[str, Any] | None
    ),
    r12_customer_validation_workflow_status: dict[str, Any] | None,
    r12_customer_trial_readiness_package: dict[str, Any] | None,
    r12_customer_trial_operational_check: dict[str, Any] | None,
    r12_customer_trial_launch_handoff_package: dict[str, Any] | None,
    r12_customer_trial_launch_packet_export: dict[str, Any] | None,
    r12_customer_trial_launch_bundle_verification: dict[str, Any] | None,
    r12_customer_field_slice_operator_rehearsal: dict[str, Any] | None,
    r12_customer_feedback_loop_operator_rehearsal: dict[str, Any] | None,
    r12_customer_trial_evidence_ledger: dict[str, Any] | None,
) -> list[dict[str, str]]:
    registry = [
        {
            "artifact_id": r12_transfer_validation["artifact_id"],
            "path": (
                "experiments/results/r12_transfer_validation/"
                "r12-transfer-validation-current-001.json"
            ),
        }
    ]
    if r12_high_risk_holdout_registry is not None:
        registry.append(
            {
                "artifact_id": r12_high_risk_holdout_registry["artifact_id"],
                "path": (
                    "experiments/results/r12_high_risk_holdout_registry/"
                    "r12-high-risk-holdout-registry-current-001.json"
                ),
            }
        )
    if r12_high_risk_holdout_transfer_replay is not None:
        registry.append(
            {
                "artifact_id": r12_high_risk_holdout_transfer_replay[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_high_risk_holdout_transfer_replay/"
                    "r12-high-risk-holdout-transfer-replay-current-001.json"
                ),
            }
        )
    if r12_recall_oriented_update is not None:
        registry.append(
            {
                "artifact_id": r12_recall_oriented_update["artifact_id"],
                "path": (
                    "experiments/results/r12_recall_oriented_update/"
                    "r12-recall-oriented-update-current-001.json"
                ),
            }
        )
    if r12_recall_update_false_alarm_stress_test is not None:
        registry.append(
            {
                "artifact_id": r12_recall_update_false_alarm_stress_test[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_update_false_alarm_stress_test/"
                    "r12-recall-update-false-alarm-stress-test-current-001.json"
                ),
            }
        )
    if r12_recall_false_alarm_mitigation_candidate is not None:
        registry.append(
            {
                "artifact_id": r12_recall_false_alarm_mitigation_candidate[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_false_alarm_mitigation_candidate/"
                    "r12-recall-false-alarm-mitigation-candidate-current-001.json"
                ),
            }
        )
    if r12_recall_mitigation_holdout_validation is not None:
        registry.append(
            {
                "artifact_id": r12_recall_mitigation_holdout_validation[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_mitigation_holdout_validation/"
                    "r12-recall-mitigation-holdout-validation-current-001.json"
                ),
            }
        )
    if r12_recall_mitigation_independent_holdout_data is not None:
        registry.append(
            {
                "artifact_id": r12_recall_mitigation_independent_holdout_data[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_mitigation_independent_holdout_data/"
                    "r12-recall-mitigation-independent-holdout-data-current-001.json"
                ),
            }
        )
    if (
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice
        is not None
    ):
        registry.append(
            {
                "artifact_id": (
                    r12_recall_mitigation_external_holdout_ingestion_or_customer_slice[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice/"
                    "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-current-001.json"
                ),
            }
        )
    if r12_external_or_customer_holdout_raw_slice is not None:
        registry.append(
            {
                "artifact_id": r12_external_or_customer_holdout_raw_slice[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_external_or_customer_holdout_raw_slice/"
                    "r12-external-or-customer-holdout-raw-slice-current-001.json"
                ),
            }
        )
    if r12_recall_mitigation_external_holdout_revalidation is not None:
        registry.append(
            {
                "artifact_id": (
                    r12_recall_mitigation_external_holdout_revalidation[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_recall_mitigation_external_holdout_revalidation/"
                    "r12-recall-mitigation-external-holdout-revalidation-current-001.json"
                ),
            }
        )
    if r12_pre_outcome_or_independent_prediction_packet is not None:
        registry.append(
            {
                "artifact_id": (
                    r12_pre_outcome_or_independent_prediction_packet[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_or_independent_prediction_packet/"
                    "r12-pre-outcome-or-independent-prediction-packet-current-001.json"
                ),
            }
        )
    if r12_independent_hindcast_revalidation is not None:
        registry.append(
            {
                "artifact_id": r12_independent_hindcast_revalidation[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_independent_hindcast_revalidation/"
                    "r12-independent-hindcast-revalidation-current-001.json"
                ),
            }
        )
    if r12_pre_outcome_prediction_trial_or_customer_field_revalidation is not None:
        registry.append(
            {
                "artifact_id": (
                    r12_pre_outcome_prediction_trial_or_customer_field_revalidation[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_prediction_trial_or_customer_field_revalidation/"
                    "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-current-001.json"
                ),
            }
        )
    if r12_pre_outcome_or_customer_field_outcome_ingestion is not None:
        registry.append(
            {
                "artifact_id": (
                    r12_pre_outcome_or_customer_field_outcome_ingestion[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_or_customer_field_outcome_ingestion/"
                    "r12-pre-outcome-or-customer-field-outcome-ingestion-current-001.json"
                ),
            }
        )
    if r12_pre_outcome_or_customer_field_outcome_revalidation is not None:
        registry.append(
            {
                "artifact_id": (
                    r12_pre_outcome_or_customer_field_outcome_revalidation[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_or_customer_field_outcome_revalidation/"
                    "r12-pre-outcome-or-customer-field-outcome-revalidation-current-001.json"
                ),
            }
        )
    if r12_target_outcome_or_customer_field_slice_arrival is not None:
        registry.append(
            {
                "artifact_id": (
                    r12_target_outcome_or_customer_field_slice_arrival[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_target_outcome_or_customer_field_slice_arrival/"
                    "r12-target-outcome-or-customer-field-slice-arrival-current-001.json"
                ),
            }
        )
    if r12_customer_field_slice_handoff_package is not None:
        registry.append(
            {
                "artifact_id": r12_customer_field_slice_handoff_package[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_slice_handoff_package/"
                    "r12-customer-field-slice-handoff-package-current-001.json"
                ),
            }
        )
    if r12_customer_field_slice_intake_validation is not None:
        registry.append(
            {
                "artifact_id": r12_customer_field_slice_intake_validation[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_slice_intake_validation/"
                    "r12-customer-field-slice-intake-validation-current-001.json"
                ),
            }
        )
    if r12_customer_field_slice_revalidation is not None:
        registry.append(
            {
                "artifact_id": r12_customer_field_slice_revalidation[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_slice_revalidation/"
                    "r12-customer-field-slice-revalidation-current-001.json"
                ),
            }
        )
    if r12_customer_field_outcome_feedback_update is not None:
        registry.append(
            {
                "artifact_id": r12_customer_field_outcome_feedback_update[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_outcome_feedback_update/"
                    "r12-customer-field-outcome-feedback-update-current-001.json"
                ),
            }
        )
    if r12_customer_feedback_update_shadow_replay is not None:
        registry.append(
            {
                "artifact_id": r12_customer_feedback_update_shadow_replay[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_feedback_update_shadow_replay/"
                    "r12-customer-feedback-update-shadow-replay-current-001.json"
                ),
            }
        )
    if r12_customer_feedback_shadow_replay_holdout_review is not None:
        registry.append(
            {
                "artifact_id": (
                    r12_customer_feedback_shadow_replay_holdout_review[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_customer_feedback_shadow_replay_holdout_review/"
                    "r12-customer-feedback-shadow-replay-holdout-review-current-001.json"
                ),
            }
        )
    if r12_customer_validation_workflow_status is not None:
        registry.append(
            {
                "artifact_id": r12_customer_validation_workflow_status[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_validation_workflow_status/"
                    "r12-customer-validation-workflow-status-current-001.json"
                ),
            }
        )
    if r12_customer_trial_readiness_package is not None:
        registry.append(
            {
                "artifact_id": r12_customer_trial_readiness_package[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_trial_readiness_package/"
                    "r12-customer-trial-readiness-package-current-001.json"
                ),
            }
        )
    if r12_customer_trial_operational_check is not None:
        registry.append(
            {
                "artifact_id": r12_customer_trial_operational_check[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_trial_operational_check/"
                    "r12-customer-trial-operational-check-current-001.json"
                ),
            }
        )
    if r12_customer_trial_launch_handoff_package is not None:
        registry.append(
            {
                "artifact_id": r12_customer_trial_launch_handoff_package[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_trial_launch_handoff_package/"
                    "r12-customer-trial-launch-handoff-package-current-001.json"
                ),
            }
        )
    if r12_customer_trial_launch_packet_export is not None:
        registry.append(
            {
                "artifact_id": r12_customer_trial_launch_packet_export[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_trial_launch_packet_export/"
                    "r12-customer-trial-launch-packet-export-current-001.json"
                ),
            }
        )
    if r12_customer_trial_launch_bundle_verification is not None:
        registry.append(
            {
                "artifact_id": r12_customer_trial_launch_bundle_verification[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_trial_launch_bundle_verification/"
                    "r12-customer-trial-launch-bundle-verification-current-001.json"
                ),
            }
        )
    if r12_customer_field_slice_operator_rehearsal is not None:
        registry.append(
            {
                "artifact_id": r12_customer_field_slice_operator_rehearsal[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_slice_operator_rehearsal/"
                    "r12-customer-field-slice-operator-rehearsal-current-001.json"
                ),
            }
        )
    if r12_customer_feedback_loop_operator_rehearsal is not None:
        registry.append(
            {
                "artifact_id": r12_customer_feedback_loop_operator_rehearsal[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_feedback_loop_operator_rehearsal/"
                    "r12-customer-feedback-loop-operator-rehearsal-current-001.json"
                ),
            }
        )
    if r12_customer_trial_evidence_ledger is not None:
        registry.append(
            {
                "artifact_id": r12_customer_trial_evidence_ledger[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/"
                    "r12_customer_trial_evidence_ledger/"
                    "r12-customer-trial-evidence-ledger-current-001.json"
                ),
            }
        )
    return registry


def _resolved_blocked_claims(
    items: list[str],
    *,
    r12_external_or_customer_holdout_raw_slice: dict[str, Any] | None,
    r12_recall_mitigation_external_holdout_revalidation: dict[str, Any] | None,
) -> list[str]:
    blocked = _unique_strings(items)
    raw_gates = (r12_external_or_customer_holdout_raw_slice or {}).get(
        "acceptance_gates",
        {},
    )
    if raw_gates.get("raw_external_or_customer_slice_present") is True:
        blocked = [
            item
            for item in blocked
            if item
            not in {
                "raw external or customer holdout slice present",
                "actual public data ingestion has completed",
            }
        ]
    revalidation_gates = (
        r12_recall_mitigation_external_holdout_revalidation or {}
    ).get("acceptance_gates", {})
    if revalidation_gates.get("external_holdout_revalidation_executed") is True:
        blocked = [
            item
            for item in blocked
            if item != "external holdout revalidation completed"
        ]
    return blocked


def _unique_strings(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--r12-high-risk-holdout-registry-path")
    parser.add_argument("--r12-high-risk-holdout-transfer-replay-path")
    parser.add_argument("--r12-recall-oriented-update-path")
    parser.add_argument("--r12-recall-update-false-alarm-stress-test-path")
    parser.add_argument("--r12-recall-false-alarm-mitigation-candidate-path")
    parser.add_argument("--r12-recall-mitigation-holdout-validation-path")
    parser.add_argument("--r12-recall-mitigation-independent-holdout-data-path")
    parser.add_argument(
        "--r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-path"
    )
    parser.add_argument("--r12-external-or-customer-holdout-raw-slice-path")
    parser.add_argument(
        "--r12-recall-mitigation-external-holdout-revalidation-path"
    )
    parser.add_argument("--r12-pre-outcome-or-independent-prediction-packet-path")
    parser.add_argument("--r12-independent-hindcast-revalidation-path")
    parser.add_argument(
        "--r12-pre-outcome-prediction-trial-or-customer-field-revalidation-path"
    )
    parser.add_argument("--r12-pre-outcome-or-customer-field-outcome-ingestion-path")
    parser.add_argument(
        "--r12-pre-outcome-or-customer-field-outcome-revalidation-path"
    )
    parser.add_argument("--r12-target-outcome-or-customer-field-slice-arrival-path")
    parser.add_argument("--r12-customer-field-slice-handoff-package-path")
    parser.add_argument("--r12-customer-field-slice-intake-validation-path")
    parser.add_argument("--r12-customer-field-slice-revalidation-path")
    parser.add_argument("--r12-customer-field-outcome-feedback-update-path")
    parser.add_argument("--r12-customer-feedback-update-shadow-replay-path")
    parser.add_argument("--r12-customer-feedback-shadow-replay-holdout-review-path")
    parser.add_argument("--r12-customer-validation-workflow-status-path")
    parser.add_argument("--r12-customer-trial-readiness-package-path")
    parser.add_argument("--r12-customer-trial-operational-check-path")
    parser.add_argument("--r12-customer-trial-launch-handoff-package-path")
    parser.add_argument("--r12-customer-trial-launch-packet-export-path")
    parser.add_argument("--r12-customer-trial-launch-bundle-verification-path")
    parser.add_argument("--r12-customer-field-slice-operator-rehearsal-path")
    parser.add_argument("--r12-customer-feedback-loop-operator-rehearsal-path")
    parser.add_argument("--r12-customer-trial-evidence-ledger-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_product_support_gate(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_transfer_validation=load_json_artifact(args.r12_transfer_validation_path),
        r12_high_risk_holdout_registry=(
            load_json_artifact(args.r12_high_risk_holdout_registry_path)
            if args.r12_high_risk_holdout_registry_path
            else None
        ),
        r12_high_risk_holdout_transfer_replay=(
            load_json_artifact(args.r12_high_risk_holdout_transfer_replay_path)
            if args.r12_high_risk_holdout_transfer_replay_path
            else None
        ),
        r12_recall_oriented_update=(
            load_json_artifact(args.r12_recall_oriented_update_path)
            if args.r12_recall_oriented_update_path
            else None
        ),
        r12_recall_update_false_alarm_stress_test=(
            load_json_artifact(
                args.r12_recall_update_false_alarm_stress_test_path
            )
            if args.r12_recall_update_false_alarm_stress_test_path
            else None
        ),
        r12_recall_false_alarm_mitigation_candidate=(
            load_json_artifact(
                args.r12_recall_false_alarm_mitigation_candidate_path
            )
            if args.r12_recall_false_alarm_mitigation_candidate_path
            else None
        ),
        r12_recall_mitigation_holdout_validation=(
            load_json_artifact(
                args.r12_recall_mitigation_holdout_validation_path
            )
            if args.r12_recall_mitigation_holdout_validation_path
            else None
        ),
        r12_recall_mitigation_independent_holdout_data=(
            load_json_artifact(
                args.r12_recall_mitigation_independent_holdout_data_path
            )
            if args.r12_recall_mitigation_independent_holdout_data_path
            else None
        ),
        r12_recall_mitigation_external_holdout_ingestion_or_customer_slice=(
            load_json_artifact(
                args.r12_recall_mitigation_external_holdout_ingestion_or_customer_slice_path
            )
            if args.r12_recall_mitigation_external_holdout_ingestion_or_customer_slice_path
            else None
        ),
        r12_external_or_customer_holdout_raw_slice=(
            load_json_artifact(args.r12_external_or_customer_holdout_raw_slice_path)
            if args.r12_external_or_customer_holdout_raw_slice_path
            else None
        ),
        r12_recall_mitigation_external_holdout_revalidation=(
            load_json_artifact(
                args.r12_recall_mitigation_external_holdout_revalidation_path
            )
            if args.r12_recall_mitigation_external_holdout_revalidation_path
            else None
        ),
        r12_pre_outcome_or_independent_prediction_packet=(
            load_json_artifact(
                args.r12_pre_outcome_or_independent_prediction_packet_path
            )
            if args.r12_pre_outcome_or_independent_prediction_packet_path
            else None
        ),
        r12_independent_hindcast_revalidation=(
            load_json_artifact(args.r12_independent_hindcast_revalidation_path)
            if args.r12_independent_hindcast_revalidation_path
            else None
        ),
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=(
            load_json_artifact(
                args.r12_pre_outcome_prediction_trial_or_customer_field_revalidation_path
            )
            if args.r12_pre_outcome_prediction_trial_or_customer_field_revalidation_path
            else None
        ),
        r12_pre_outcome_or_customer_field_outcome_ingestion=(
            load_json_artifact(
                args.r12_pre_outcome_or_customer_field_outcome_ingestion_path
            )
            if args.r12_pre_outcome_or_customer_field_outcome_ingestion_path
            else None
        ),
        r12_pre_outcome_or_customer_field_outcome_revalidation=(
            load_json_artifact(
                args.r12_pre_outcome_or_customer_field_outcome_revalidation_path
            )
            if args.r12_pre_outcome_or_customer_field_outcome_revalidation_path
            else None
        ),
        r12_target_outcome_or_customer_field_slice_arrival=(
            load_json_artifact(
                args.r12_target_outcome_or_customer_field_slice_arrival_path
            )
            if args.r12_target_outcome_or_customer_field_slice_arrival_path
            else None
        ),
        r12_customer_field_slice_handoff_package=(
            load_json_artifact(args.r12_customer_field_slice_handoff_package_path)
            if args.r12_customer_field_slice_handoff_package_path
            else None
        ),
        r12_customer_field_slice_intake_validation=(
            load_json_artifact(args.r12_customer_field_slice_intake_validation_path)
            if args.r12_customer_field_slice_intake_validation_path
            else None
        ),
        r12_customer_field_slice_revalidation=(
            load_json_artifact(args.r12_customer_field_slice_revalidation_path)
            if args.r12_customer_field_slice_revalidation_path
            else None
        ),
        r12_customer_field_outcome_feedback_update=(
            load_json_artifact(
                args.r12_customer_field_outcome_feedback_update_path
            )
            if args.r12_customer_field_outcome_feedback_update_path
            else None
        ),
        r12_customer_feedback_update_shadow_replay=(
            load_json_artifact(
                args.r12_customer_feedback_update_shadow_replay_path
            )
            if args.r12_customer_feedback_update_shadow_replay_path
            else None
        ),
        r12_customer_feedback_shadow_replay_holdout_review=(
            load_json_artifact(
                args.r12_customer_feedback_shadow_replay_holdout_review_path
            )
            if args.r12_customer_feedback_shadow_replay_holdout_review_path
            else None
        ),
        r12_customer_validation_workflow_status=(
            load_json_artifact(args.r12_customer_validation_workflow_status_path)
            if args.r12_customer_validation_workflow_status_path
            else None
        ),
        r12_customer_trial_readiness_package=(
            load_json_artifact(args.r12_customer_trial_readiness_package_path)
            if args.r12_customer_trial_readiness_package_path
            else None
        ),
        r12_customer_trial_operational_check=(
            load_json_artifact(args.r12_customer_trial_operational_check_path)
            if args.r12_customer_trial_operational_check_path
            else None
        ),
        r12_customer_trial_launch_handoff_package=(
            load_json_artifact(args.r12_customer_trial_launch_handoff_package_path)
            if args.r12_customer_trial_launch_handoff_package_path
            else None
        ),
        r12_customer_trial_launch_packet_export=(
            load_json_artifact(args.r12_customer_trial_launch_packet_export_path)
            if args.r12_customer_trial_launch_packet_export_path
            else None
        ),
        r12_customer_trial_launch_bundle_verification=(
            load_json_artifact(
                args.r12_customer_trial_launch_bundle_verification_path
            )
            if args.r12_customer_trial_launch_bundle_verification_path
            else None
        ),
        r12_customer_field_slice_operator_rehearsal=(
            load_json_artifact(
                args.r12_customer_field_slice_operator_rehearsal_path
            )
            if args.r12_customer_field_slice_operator_rehearsal_path
            else None
        ),
        r12_customer_feedback_loop_operator_rehearsal=(
            load_json_artifact(
                args.r12_customer_feedback_loop_operator_rehearsal_path
            )
            if args.r12_customer_feedback_loop_operator_rehearsal_path
            else None
        ),
        r12_customer_trial_evidence_ledger=(
            load_json_artifact(args.r12_customer_trial_evidence_ledger_path)
            if args.r12_customer_trial_evidence_ledger_path
            else None
        ),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
