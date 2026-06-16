from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_case_matrix import build_r6_case_matrix
from experiments.r6_ccfa_readiness_report import build_r6_ccfa_readiness_report
from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_cross_case_transfer_protocol import build_r6_cross_case_transfer_protocol
from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics
from experiments.r6_false_alarm_discriminator import (
    build_r6_false_alarm_discriminator,
)
from experiments.r6_followup_holdout_validation import build_r6_followup_holdout_validation
from experiments.r6_in_condition_holdout_ledger import build_r6_in_condition_holdout_ledger
from experiments.r6_interaction_signal_validity import (
    build_r6_interaction_signal_validity,
)
from experiments.r6_interaction_signal_validity_holdout_validation import (
    build_r6_interaction_signal_validity_holdout_validation,
)
from experiments.r6_mechanism_cap_ablation import build_r6_mechanism_cap_ablation
from experiments.r6_mechanism_research_readiness_report import (
    build_r6_mechanism_research_readiness_report,
)
from experiments.r6_product_evidence_cards import build_r6_product_evidence_cards
from experiments.r6_product_report import build_r6_product_report
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy
from experiments.r6_risk_discovery_holdout_validation import (
    build_r6_risk_discovery_holdout_validation,
)
from experiments.r6_risk_discovery_threshold_sweep import (
    build_r6_risk_discovery_threshold_sweep,
)
from experiments.r6_risk_discovery_value_report import (
    build_r6_risk_discovery_value_report,
)


R6_EVIDENCE_REPORT_SCHEMA_VERSION = "r6-evidence-report-v1"


def build_r6_evidence_report(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    public_proxy = build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-public-outcome-proxy",
        run_id=run_id,
    )
    second_public_proxy = build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-public-outcome-proxy-anes-health",
        run_id=run_id,
        source_key="anes_health_heldout",
    )
    third_public_proxy = build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-public-outcome-proxy-anes-climate",
        run_id=run_id,
        source_key="anes_climate_heldout",
    )
    public_proxies = [public_proxy, second_public_proxy, third_public_proxy]
    case_matrix = build_r6_case_matrix(
        artifact_id=f"{artifact_id}-case-matrix",
        run_id=run_id,
        public_outcome_proxies=[public_proxy, second_public_proxy],
    )
    mechanism_cap_ablation = build_r6_mechanism_cap_ablation(
        artifact_id=f"{artifact_id}-mechanism-cap-ablation",
        run_id=run_id,
    )
    product_report = build_r6_product_report(
        artifact_id=f"{artifact_id}-product-report",
        run_id=run_id,
        case_matrix=case_matrix,
        mechanism_cap_ablation=mechanism_cap_ablation,
    )
    followup_holdout = build_r6_followup_holdout_validation(
        artifact_id=f"{artifact_id}-followup-holdout-validation",
        run_id=run_id,
    )
    transfer_protocol = build_r6_cross_case_transfer_protocol(
        artifact_id=f"{artifact_id}-cross-case-transfer-protocol",
        run_id=run_id,
    )
    holdout_ledger = build_r6_in_condition_holdout_ledger(
        artifact_id=f"{artifact_id}-in-condition-holdout-ledger",
        run_id=run_id,
    )
    mechanism_research_readiness = build_r6_mechanism_research_readiness_report(
        artifact_id=f"{artifact_id}-mechanism-research-readiness-report",
        run_id=run_id,
    )
    product_evidence_cards = build_r6_product_evidence_cards(
        artifact_id=f"{artifact_id}-product-evidence-cards",
        run_id=run_id,
        product_report=product_report,
        transfer_protocol=transfer_protocol,
        holdout_ledger=holdout_ledger,
        mechanism_research_readiness_report=mechanism_research_readiness,
    )
    ablation = build_r6_ablation_report(
        artifact_id=f"{artifact_id}-ablation",
        run_id=run_id,
        public_outcome_proxy=public_proxy,
    )
    second_ablation = build_r6_ablation_report(
        artifact_id=f"{artifact_id}-ablation-anes-health",
        run_id=run_id,
        public_outcome_proxy=second_public_proxy,
    )
    third_ablation = build_r6_ablation_report(
        artifact_id=f"{artifact_id}-ablation-anes-climate",
        run_id=run_id,
        public_outcome_proxy=third_public_proxy,
    )
    decision_value_metrics = build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value-metrics",
        run_id=run_id,
        ablation_reports=[ablation, second_ablation, third_ablation],
    )
    risk_discovery_holdout_validation = build_r6_risk_discovery_holdout_validation(
        artifact_id=f"{artifact_id}-risk-discovery-holdout-validation",
        run_id=run_id,
        decision_value_metrics=decision_value_metrics,
    )
    risk_discovery_threshold_sweep = build_r6_risk_discovery_threshold_sweep(
        artifact_id=f"{artifact_id}-risk-discovery-threshold-sweep",
        run_id=run_id,
    )
    false_alarm_discriminator = build_r6_false_alarm_discriminator(
        artifact_id=f"{artifact_id}-false-alarm-discriminator",
        run_id=run_id,
        decision_value_metrics=decision_value_metrics,
    )
    interaction_signal_validity = build_r6_interaction_signal_validity(
        artifact_id=f"{artifact_id}-interaction-signal-validity",
        run_id=run_id,
        decision_value_metrics=decision_value_metrics,
    )
    interaction_signal_validity_holdout_validation = (
        build_r6_interaction_signal_validity_holdout_validation(
            artifact_id=f"{artifact_id}-interaction-signal-validity-holdout-validation",
            run_id=run_id,
            interaction_signal_validity=interaction_signal_validity,
        )
    )
    risk_discovery_value = build_r6_risk_discovery_value_report(
        artifact_id=f"{artifact_id}-risk-discovery-value-report",
        run_id=run_id,
        transfer_protocol=transfer_protocol,
        holdout_ledger=holdout_ledger,
        product_evidence_cards=product_evidence_cards,
        decision_value_metrics=decision_value_metrics,
        risk_discovery_threshold_sweep=risk_discovery_threshold_sweep,
        false_alarm_discriminator=false_alarm_discriminator,
        interaction_signal_validity=interaction_signal_validity,
        interaction_signal_validity_holdout_validation=(
            interaction_signal_validity_holdout_validation
        ),
        risk_discovery_holdout_validation=risk_discovery_holdout_validation,
    )
    ccfa_readiness = build_r6_ccfa_readiness_report(
        artifact_id=f"{artifact_id}-ccfa-readiness-report",
        run_id=run_id,
        transfer_protocol=transfer_protocol,
        holdout_ledger=holdout_ledger,
        product_evidence_cards=product_evidence_cards,
        risk_discovery_value_report=risk_discovery_value,
    )
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    prior_anchored_beats_no_interaction = (
        by_method["prior_anchored_interaction"]["mean_absolute_error"]
        < by_method["no_interaction_prior"]["mean_absolute_error"]
    )
    report = {
        "schema_version": R6_EVIDENCE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "public_proxy_evidence_ready",
        "evidence_answer": {
            "current_decision": "continue_r6_with_constraints",
            "stoploss_triggered": False,
            "reason": (
                "Three public proxies are connected. One supports the prior-anchored "
                "interaction signal, two expose non-improvement boundaries, and global "
                "updates remain blocked. This is still worth continuing as risk "
                "discovery because the static prior is the simulation base, not the "
                "research opponent."
            ),
        },
        "public_outcome_proxies": [
            _public_proxy_summary(proxy) for proxy in public_proxies
        ],
        "public_outcome_proxy": {
            "artifact_id": public_proxy["artifact_id"],
            "target_case_id": public_proxy["target_case_id"],
            "usable_row_count": public_proxy["public_source"]["usable_row_count"],
            "source_url": public_proxy["public_source"]["source_url"],
            "observed_reject_proxy": public_proxy["metrics"]["observed_reject_proxy"],
        },
        "case_matrix_summary": {
            "artifact_id": case_matrix["artifact_id"],
            "case_count": case_matrix["case_count"],
            "public_outcome_proxy_case_count": case_matrix["public_outcome_proxy_case_count"],
        },
        "ablation_summary": {
            "artifact_id": ablation["artifact_id"],
            "prior_anchored_beats_no_interaction": prior_anchored_beats_no_interaction,
            "no_interaction_error": by_method["no_interaction_prior"]["mean_absolute_error"],
            "prior_anchored_error": by_method["prior_anchored_interaction"][
                "mean_absolute_error"
            ],
            "outcome_feedback_update_error": by_method["outcome_feedback_update"][
                "mean_absolute_error"
            ],
            "outcome_feedback_global_status": by_method["outcome_feedback_update"][
                "global_update_status"
            ],
            "current_best_non_feedback_method": ablation["current_best_non_feedback_method"],
        },
        "ablation_reports": [
            _ablation_case_summary(ablation),
            _ablation_case_summary(second_ablation),
            _ablation_case_summary(third_ablation),
        ],
        "multi_proxy_summary": _multi_proxy_summary(
            [ablation, second_ablation, third_ablation]
        ),
        "product_report_summary": {
            "artifact_id": product_report["artifact_id"],
            "status": product_report["status"],
            "market_claim_status": product_report["decision_support"]["market_claim_status"],
            "mechanism_cap_status": product_report["mechanism_cap_review"][
                "claim_status"
            ],
        },
        "followup_holdout_validation_summary": {
            "artifact_id": followup_holdout["artifact_id"],
            "status": followup_holdout["status"],
            "mechanism_cap_upgrade_status": followup_holdout[
                "mechanism_cap_validation"
            ]["upgrade_status"],
            "outcome_feedback_upgrade_status": followup_holdout[
                "outcome_feedback_validation"
            ]["upgrade_status"],
            "global_update_accepted": followup_holdout["acceptance_gates"][
                "global_update_accepted"
            ],
        },
        "cross_case_transfer_protocol_summary": {
            "artifact_id": transfer_protocol["artifact_id"],
            "status": transfer_protocol["status"],
            "mechanism_cap_l4_in_condition_transfer_passed": transfer_protocol[
                "acceptance_gates"
            ]["mechanism_cap_l4_in_condition_transfer_passed"],
            "outcome_feedback_transfer_beats_prior_interaction": transfer_protocol[
                "acceptance_gates"
            ]["outcome_feedback_transfer_beats_prior_interaction"],
            "outcome_feedback_transfer_beats_static_prior": transfer_protocol[
                "acceptance_gates"
            ]["outcome_feedback_transfer_beats_static_prior"],
            "runtime_update_guard_passed": transfer_protocol["acceptance_gates"][
                "runtime_update_guard_passed"
            ],
            "risk_discovery_value_path_open": transfer_protocol[
                "acceptance_gates"
            ]["risk_discovery_value_path_open"],
            "global_update_accepted": transfer_protocol["acceptance_gates"][
                "global_update_accepted"
            ],
        },
        "in_condition_holdout_ledger_summary": {
            "artifact_id": holdout_ledger["artifact_id"],
            "status": holdout_ledger["status"],
            "in_condition_holdout_count": holdout_ledger["summary"][
                "in_condition_holdout_count"
            ],
            "global_update_data_gate_passed": holdout_ledger["summary"][
                "global_update_data_gate_passed"
            ],
        },
        "product_evidence_cards_summary": {
            "artifact_id": product_evidence_cards["artifact_id"],
            "status": product_evidence_cards["status"],
            "card_count": product_evidence_cards["card_count"],
            "static_narrative_fallback_allowed": product_evidence_cards[
                "demo_api_contract"
            ]["static_narrative_fallback_allowed"],
        },
        "mechanism_research_readiness_summary": {
            "artifact_id": mechanism_research_readiness["artifact_id"],
            "status": mechanism_research_readiness["status"],
            "mechanism_mvp_result": mechanism_research_readiness["decision"][
                "mechanism_mvp_result"
            ],
            "ccf_a_main_contribution_ready": mechanism_research_readiness[
                "decision"
            ]["ccf_a_main_contribution_ready"],
            "runtime_default_allowed": mechanism_research_readiness["decision"][
                "runtime_default_allowed"
            ],
        },
        "decision_value_metrics_summary": {
            "artifact_id": decision_value_metrics["artifact_id"],
            "status": decision_value_metrics["status"],
            "decision_value_passed": decision_value_metrics["decision_value_passed"],
            "static_prior_miss_recovery_rate": decision_value_metrics["summary"][
                "static_prior_miss_recovery_rate"
            ],
            "top_k_risk_hit_rate": decision_value_metrics["summary"][
                "top_k_risk_hit_rate"
            ],
            "false_alarm_rate": decision_value_metrics["summary"][
                "false_alarm_rate"
            ],
        },
        "risk_discovery_holdout_validation_summary": {
            "artifact_id": risk_discovery_holdout_validation["artifact_id"],
            "status": risk_discovery_holdout_validation["status"],
            "risk_discovery_holdout_passed": risk_discovery_holdout_validation[
                "acceptance_gates"
            ]["risk_discovery_holdout_passed"],
            "same_family_trial_count": risk_discovery_holdout_validation["summary"][
                "same_family_trial_count"
            ],
            "passed_trial_count": risk_discovery_holdout_validation["summary"][
                "passed_trial_count"
            ],
        },
        "risk_discovery_threshold_sweep_summary": {
            "artifact_id": risk_discovery_threshold_sweep["artifact_id"],
            "status": risk_discovery_threshold_sweep["status"],
            "passing_threshold_found": risk_discovery_threshold_sweep[
                "acceptance_gates"
            ]["passing_threshold_found"],
            "separating_threshold_found": risk_discovery_threshold_sweep[
                "acceptance_gates"
            ]["separating_threshold_found"],
            "false_alarm_reducible_by_threshold": risk_discovery_threshold_sweep[
                "summary"
            ]["false_alarm_reducible_by_threshold"],
            "best_threshold": risk_discovery_threshold_sweep["summary"][
                "best_threshold"
            ],
            "true_signal_false_alarm_delta_overlap": risk_discovery_threshold_sweep[
                "summary"
            ]["true_signal_false_alarm_delta_overlap"],
        },
        "false_alarm_discriminator_summary": {
            "artifact_id": false_alarm_discriminator["artifact_id"],
            "status": false_alarm_discriminator["status"],
            "current_proxy_separation_found": false_alarm_discriminator[
                "acceptance_gates"
            ]["current_proxy_separation_found"],
            "pre_outcome_safe_candidate_found": false_alarm_discriminator[
                "acceptance_gates"
            ]["pre_outcome_safe_candidate_found"],
            "generalizable_discriminator_found": false_alarm_discriminator[
                "acceptance_gates"
            ]["generalizable_discriminator_found"],
            "accepted_candidate_count": false_alarm_discriminator["summary"][
                "accepted_candidate_count"
            ],
            "false_alarm_discriminator_ready": false_alarm_discriminator[
                "acceptance_gates"
            ]["false_alarm_discriminator_ready"],
        },
        "interaction_signal_validity_summary": {
            "artifact_id": interaction_signal_validity["artifact_id"],
            "status": interaction_signal_validity["status"],
            "mean_validity_score": interaction_signal_validity["summary"][
                "mean_validity_score"
            ],
            "current_proxy_supported_signal_count": interaction_signal_validity[
                "summary"
            ]["current_proxy_supported_signal_count"],
            "rejected_false_alarm_count": interaction_signal_validity["summary"][
                "rejected_false_alarm_count"
            ],
            "accepted_count": interaction_signal_validity["summary"][
                "accepted_count"
            ],
            "interaction_signal_validity_generalized": (
                interaction_signal_validity["acceptance_gates"][
                    "interaction_signal_validity_generalized"
                ]
            ),
        },
        "interaction_signal_validity_holdout_summary": {
            "artifact_id": interaction_signal_validity_holdout_validation["artifact_id"],
            "status": interaction_signal_validity_holdout_validation["status"],
            "source_supported_count": interaction_signal_validity_holdout_validation[
                "summary"
            ]["source_supported_count"],
            "eligible_independent_holdout_count": (
                interaction_signal_validity_holdout_validation["summary"][
                    "eligible_independent_holdout_count"
                ]
            ),
            "passed_holdout_count": interaction_signal_validity_holdout_validation[
                "summary"
            ]["passed_holdout_count"],
            "contradicted_holdout_count": (
                interaction_signal_validity_holdout_validation["summary"][
                    "contradicted_holdout_count"
                ]
            ),
            "interaction_signal_validity_holdout_passed": (
                interaction_signal_validity_holdout_validation["acceptance_gates"][
                    "interaction_signal_validity_holdout_passed"
                ]
            ),
        },
        "risk_discovery_value_summary": {
            "artifact_id": risk_discovery_value["artifact_id"],
            "status": risk_discovery_value["status"],
            "static_prior_role": risk_discovery_value["objective_reframe"][
                "static_prior_role"
            ],
            "r6_overall_worth_continuing": risk_discovery_value["decision"][
                "r6_overall_worth_continuing"
            ],
            "runtime_update_default_ready": risk_discovery_value["decision"][
                "runtime_update_default_ready"
            ],
            "decision_value_passed": risk_discovery_value["decision_value_summary"][
                "decision_value_passed"
            ],
            "risk_discovery_holdout_passed": risk_discovery_value[
                "holdout_validation_summary"
            ]["risk_discovery_holdout_passed"],
            "false_alarm_discriminator_ready": risk_discovery_value[
                "false_alarm_discriminator_summary"
            ]["false_alarm_discriminator_ready"],
            "interaction_signal_validity_generalized": risk_discovery_value[
                "interaction_signal_validity_summary"
            ]["interaction_signal_validity_generalized"],
            "interaction_signal_validity_holdout_passed": risk_discovery_value[
                "interaction_signal_validity_holdout_summary"
            ]["interaction_signal_validity_holdout_passed"],
        },
        "ccfa_readiness_summary": {
            "artifact_id": ccfa_readiness["artifact_id"],
            "status": ccfa_readiness["status"],
            "ccf_a_main_contribution_ready": ccfa_readiness["verdict"][
                "ccf_a_main_contribution_ready"
            ],
            "readiness_level": ccfa_readiness["verdict"]["readiness_level"],
            "failed_required_gate_count": ccfa_readiness[
                "failed_required_gate_count"
            ],
        },
        "acceptance_gates": {
            "public_outcome_proxy_connected": True,
            "second_public_outcome_proxy_connected": True,
            "third_public_outcome_proxy_connected": True,
            "ablation_baselines_present": _has_required_ablation_methods(ablation),
            "deterministic_replay_passed": (
                ablation["deterministic_replay"]["passed"]
                and second_ablation["deterministic_replay"]["passed"]
                and third_ablation["deterministic_replay"]["passed"]
            ),
            "product_report_ingests_mechanism_cap": True,
            "followup_holdout_validation_present": True,
            "mechanism_cap_same_family_holdout_available": followup_holdout[
                "acceptance_gates"
            ]["mechanism_cap_same_family_holdout_available"],
            "mechanism_cap_same_family_cap_condition_covered": followup_holdout[
                "acceptance_gates"
            ]["mechanism_cap_same_family_cap_condition_covered"],
            "mechanism_cap_same_family_validation_passed": followup_holdout[
                "acceptance_gates"
            ]["mechanism_cap_same_family_validation_passed"],
            "outcome_feedback_cross_case_transfer_available": followup_holdout[
                "acceptance_gates"
            ]["outcome_feedback_cross_case_transfer_available"],
            "cross_case_transfer_protocol_present": True,
            "outcome_feedback_transfer_beats_static_prior": transfer_protocol[
                "acceptance_gates"
            ]["outcome_feedback_transfer_beats_static_prior"],
            "runtime_update_guard_passed": transfer_protocol["acceptance_gates"][
                "runtime_update_guard_passed"
            ],
            "decision_value_metrics_present": True,
            "decision_value_passed": decision_value_metrics["decision_value_passed"],
            "risk_discovery_holdout_validation_present": True,
            "risk_discovery_holdout_passed": risk_discovery_holdout_validation[
                "acceptance_gates"
            ]["risk_discovery_holdout_passed"],
            "risk_discovery_threshold_sweep_present": True,
            "threshold_tuning_sufficient": risk_discovery_threshold_sweep[
                "decision"
            ]["threshold_tuning_sufficient"],
            "false_alarm_reducible_by_threshold": risk_discovery_threshold_sweep[
                "summary"
            ]["false_alarm_reducible_by_threshold"],
            "false_alarm_discriminator_present": True,
            "false_alarm_discriminator_ready": false_alarm_discriminator[
                "acceptance_gates"
            ]["false_alarm_discriminator_ready"],
            "generalizable_false_alarm_discriminator_found": false_alarm_discriminator[
                "acceptance_gates"
            ]["generalizable_discriminator_found"],
            "interaction_signal_validity_present": True,
            "interaction_signal_validity_generalized": interaction_signal_validity[
                "acceptance_gates"
            ]["interaction_signal_validity_generalized"],
            "current_proxy_supported_interaction_signal_observed": (
                interaction_signal_validity["acceptance_gates"][
                    "current_proxy_supported_signal_observed"
                ]
            ),
            "interaction_signal_validity_holdout_validation_present": True,
            "interaction_signal_validity_holdout_passed": (
                interaction_signal_validity_holdout_validation["acceptance_gates"][
                    "interaction_signal_validity_holdout_passed"
                ]
            ),
            "risk_discovery_value_report_present": True,
            "static_prior_role_reframed_as_foundation": (
                risk_discovery_value["objective_reframe"]["static_prior_role"]
                == "foundation_not_opponent"
            ),
            "risk_discovery_path_should_continue": risk_discovery_value[
                "decision"
            ]["r6_overall_worth_continuing"],
            "in_condition_holdout_ledger_present": True,
            "in_condition_holdout_found": holdout_ledger["summary"][
                "in_condition_holdout_count"
            ]
            > 0,
            "product_evidence_cards_present": True,
            "mechanism_driven_mvp_summary_present": True,
            "product_guard_preserved": (
                mechanism_research_readiness["readiness_gates"][
                    "product_guard_preserved"
                ]
                and product_evidence_cards["demo_api_contract"][
                    "static_narrative_fallback_allowed"
                ]
                is False
                and "accuracy_claim_blocked" in product_evidence_cards["risk_flags"]
            ),
            "ccfa_readiness_report_present": True,
            "ccf_a_main_contribution_ready": ccfa_readiness["verdict"][
                "ccf_a_main_contribution_ready"
            ],
            "global_update_accepted": False,
        },
        "remaining_gaps": _remaining_gaps_with_method_gates(
            followup_holdout=followup_holdout,
            transfer_protocol=transfer_protocol,
            holdout_ledger=holdout_ledger,
            decision_value_metrics=decision_value_metrics,
            risk_discovery_holdout_validation=risk_discovery_holdout_validation,
            risk_discovery_threshold_sweep=risk_discovery_threshold_sweep,
            false_alarm_discriminator=false_alarm_discriminator,
            interaction_signal_validity=interaction_signal_validity,
            interaction_signal_validity_holdout_validation=(
                interaction_signal_validity_holdout_validation
            ),
            risk_discovery_value=risk_discovery_value,
            ccfa_readiness=ccfa_readiness,
            mechanism_research_readiness=mechanism_research_readiness,
        ),
        "source_refs": [
            public_proxy["artifact_id"],
            second_public_proxy["artifact_id"],
            third_public_proxy["artifact_id"],
            case_matrix["artifact_id"],
            product_report["artifact_id"],
            mechanism_cap_ablation["artifact_id"],
            followup_holdout["artifact_id"],
            transfer_protocol["artifact_id"],
            holdout_ledger["artifact_id"],
            mechanism_research_readiness["artifact_id"],
            product_evidence_cards["artifact_id"],
            decision_value_metrics["artifact_id"],
            risk_discovery_holdout_validation["artifact_id"],
            risk_discovery_threshold_sweep["artifact_id"],
            false_alarm_discriminator["artifact_id"],
            interaction_signal_validity["artifact_id"],
            interaction_signal_validity_holdout_validation["artifact_id"],
            risk_discovery_value["artifact_id"],
            ccfa_readiness["artifact_id"],
            ablation["artifact_id"],
            second_ablation["artifact_id"],
            third_ablation["artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "This is public proxy evidence only; it is not field validation.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "public_proxy_not_field_validation",
            "same_case_feedback_not_global_acceptance",
            "not_cross_domain_accuracy_evidence",
            "mixed_public_proxy_evidence",
            "mechanism_cap_not_runtime_default",
            "partial_holdout_not_runtime_acceptance",
            "static_prior_is_foundation_not_opponent",
            "false_alarm_discriminator_not_runtime_ready",
            "interaction_signal_validity_not_generalized",
            "mechanism_research_diagnostic_only",
            "ccf_a_main_contribution_not_ready",
        ],
        "blocking_gaps": [
            "global_update_acceptance_blocked",
            "cross_case_validation_missing",
            "ccf_a_readiness_failed",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_evidence_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_evidence_report(**kwargs))


def _remaining_gaps_with_method_gates(
    *,
    followup_holdout: dict[str, Any],
    transfer_protocol: dict[str, Any],
    holdout_ledger: dict[str, Any],
    decision_value_metrics: dict[str, Any],
    risk_discovery_holdout_validation: dict[str, Any],
    risk_discovery_threshold_sweep: dict[str, Any],
    false_alarm_discriminator: dict[str, Any],
    interaction_signal_validity: dict[str, Any],
    interaction_signal_validity_holdout_validation: dict[str, Any],
    risk_discovery_value: dict[str, Any],
    ccfa_readiness: dict[str, Any],
    mechanism_research_readiness: dict[str, Any],
) -> list[str]:
    gaps = [
        "needs_more_public_or_real_outcomes",
        "needs_holdout_case_for_feedback_update_acceptance",
        "needs_holdout_case_for_mechanism_cap_acceptance",
    ]
    gaps.extend(followup_holdout["blocking_gaps"])
    gaps.extend(transfer_protocol["blocking_gaps"])
    gaps.extend(holdout_ledger["blocking_gaps"])
    gaps.extend(decision_value_metrics["blocking_gaps"])
    gaps.extend(risk_discovery_holdout_validation["blocking_gaps"])
    gaps.extend(
        _threshold_gaps_after_discriminator(
            risk_discovery_threshold_sweep=risk_discovery_threshold_sweep,
            false_alarm_discriminator=false_alarm_discriminator,
        )
    )
    gaps.extend(
        _false_alarm_gaps_after_signal_validity(
            false_alarm_discriminator=false_alarm_discriminator,
            interaction_signal_validity=interaction_signal_validity,
        )
    )
    gaps.extend(interaction_signal_validity["blocking_gaps"])
    gaps.extend(interaction_signal_validity_holdout_validation["blocking_gaps"])
    gaps.extend(risk_discovery_value["blocking_gaps"])
    gaps.extend(ccfa_readiness["blocking_gaps"])
    gaps.extend(mechanism_research_readiness["blocking_gaps"])
    return sorted(set(gaps))


def _threshold_gaps_after_discriminator(
    *,
    risk_discovery_threshold_sweep: dict[str, Any],
    false_alarm_discriminator: dict[str, Any],
) -> list[str]:
    if not false_alarm_discriminator["acceptance_gates"][
        "false_alarm_discriminator_present"
    ]:
        return risk_discovery_threshold_sweep["blocking_gaps"]
    return [
        gap
        for gap in risk_discovery_threshold_sweep["blocking_gaps"]
        if gap != "needs_non_threshold_false_alarm_discriminator"
    ]


def _false_alarm_gaps_after_signal_validity(
    *,
    false_alarm_discriminator: dict[str, Any],
    interaction_signal_validity: dict[str, Any],
) -> list[str]:
    if interaction_signal_validity["acceptance_gates"][
        "interaction_signal_validity_present"
    ]:
        return []
    return false_alarm_discriminator["blocking_gaps"]


def _public_proxy_summary(proxy: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": proxy["artifact_id"],
        "source_key": proxy["source_key"],
        "target_case_id": proxy["target_case_id"],
        "source_artifact_id": proxy["public_source"]["source_artifact_id"],
        "source_name": proxy["public_source"]["source_name"],
        "usable_row_count": proxy["public_source"]["usable_row_count"],
        "observed_reject_proxy": proxy["metrics"]["observed_reject_proxy"],
        "mapping_target_response_option": proxy["mapping_review"]["target_response_option"],
    }


def _ablation_case_summary(ablation: dict[str, Any]) -> dict[str, Any]:
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    prior_anchored_beats_no_interaction = (
        by_method["prior_anchored_interaction"]["mean_absolute_error"]
        < by_method["no_interaction_prior"]["mean_absolute_error"]
    )
    return {
        "artifact_id": ablation["artifact_id"],
        "target_case_id": ablation["target_case_id"],
        "public_proxy_observed_reject": ablation["public_proxy"]["observed_reject_proxy"],
        "no_interaction_error": by_method["no_interaction_prior"]["mean_absolute_error"],
        "prior_anchored_error": by_method["prior_anchored_interaction"][
            "mean_absolute_error"
        ],
        "prior_anchored_beats_no_interaction": prior_anchored_beats_no_interaction,
        "outcome_feedback_global_status": by_method["outcome_feedback_update"][
            "global_update_status"
        ],
    }


def _multi_proxy_summary(ablation_reports: list[dict[str, Any]]) -> dict[str, Any]:
    case_summaries = [_ablation_case_summary(ablation) for ablation in ablation_reports]
    positive_count = sum(
        1 for summary in case_summaries if summary["prior_anchored_beats_no_interaction"]
    )
    regression_count = len(case_summaries) - positive_count
    return {
        "public_proxy_count": len(case_summaries),
        "public_proxy_source_count": len(
            {summary["target_case_id"] for summary in case_summaries}
        ),
        "prior_anchored_positive_count": positive_count,
        "prior_anchored_regression_count": regression_count,
        "conclusion": (
            "mixed_public_proxy_evidence"
            if regression_count
            else "positive_public_proxy_evidence"
        ),
    }


def _has_required_ablation_methods(ablation: dict[str, Any]) -> bool:
    methods = {result["method"] for result in ablation["baseline_results"]}
    required = {
        "no_interaction_prior",
        "random_noise_baseline",
        "uncalibrated_interaction",
        "prior_anchored_interaction",
        "outcome_feedback_update",
    }
    return required <= methods


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_evidence_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "decision": report["evidence_answer"]["current_decision"],
                "output": str(output_path),
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
