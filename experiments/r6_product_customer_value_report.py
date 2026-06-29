from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_product_decision_report import build_r6_product_decision_report
from experiments.r6_product_claim_evidence_registry import (
    build_r6_product_claim_evidence_registry,
    build_r6_research_product_value_support_v2,
)
from experiments.r6_learning_counterfactual_holdout_validation import (
    build_r6_learning_counterfactual_holdout_validation,
)
from experiments.r6_learning_counterfactual_simulator import (
    build_r6_learning_counterfactual_simulator,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_PRODUCT_CUSTOMER_VALUE_REPORT_SCHEMA_VERSION = (
    "r6-product-customer-value-report-v1"
)
R6_PRODUCT_CUSTOMER_VALUE_SECTIONS = [
    "static_prior_baseline",
    "trend_direction",
    "risk_interval",
    "risk_distribution",
    "abnormal_segments",
    "mechanism_explanation",
    "counterfactual_policy_comparison",
    "research_support_gap_ledger",
    "evidence_and_blocked_claims",
    "outcome_review_plan",
]


def build_r6_product_customer_value_report(
    *,
    artifact_id: str,
    run_id: str,
    decision_report: dict[str, Any] | None = None,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    value_support: dict[str, Any] | None = None,
    learning_counterfactual_simulator: dict[str, Any] | None = None,
    learning_counterfactual_holdout_validation: dict[str, Any] | None = None,
    r8_robustness_holdout_gate: dict[str, Any] | None = None,
    r8_stop_loss_diagnosis: dict[str, Any] | None = None,
    r8_product_failure_diagnosis_package: dict[str, Any] | None = None,
    r9_combination_comparison: dict[str, Any] | None = None,
    r9_synthetic_mechanism_lab: dict[str, Any] | None = None,
    r9_false_alarm_gate_redesign: dict[str, Any] | None = None,
    r9_holdout_guard: dict[str, Any] | None = None,
    r11_product_shadow_trial: dict[str, Any] | None = None,
    r12_product_support_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    decision = decision_report or build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-current-001",
        run_id=run_id,
    )
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-current-001",
        run_id=run_id,
    )
    counterfactual = (
        learning_counterfactual_simulator
        or build_r6_learning_counterfactual_simulator(
            artifact_id="r6-learning-counterfactual-simulator-current-001",
            run_id=run_id,
            trend_interval_risk_metrics=metrics,
        )
    )
    counterfactual_holdout = (
        learning_counterfactual_holdout_validation
        or build_r6_learning_counterfactual_holdout_validation(
            artifact_id="r6-learning-counterfactual-holdout-validation-current-001",
            run_id=run_id,
            trend_interval_risk_metrics=metrics,
            learning_counterfactual_simulator=counterfactual,
        )
    )
    if value_support is None:
        claim_registry = build_r6_product_claim_evidence_registry(
            artifact_id="r6-product-claim-evidence-registry-current-001",
            run_id=run_id,
            learning_counterfactual_simulator=counterfactual,
            learning_counterfactual_holdout_validation=counterfactual_holdout,
        )
        support = build_r6_research_product_value_support_v2(
            artifact_id="r6-research-product-value-support-v2-current-001",
            run_id=run_id,
            claim_evidence_registry=claim_registry,
        )
    else:
        support = value_support
    frontend_demo_ready = _frontend_demo_ready()
    source_registry = _source_registry(
        decision,
        metrics,
        support,
        counterfactual,
        counterfactual_holdout,
        r8_robustness_holdout_gate,
        r8_stop_loss_diagnosis,
        r8_product_failure_diagnosis_package,
        r9_combination_comparison,
        r9_synthetic_mechanism_lab,
        r9_false_alarm_gate_redesign,
        r9_holdout_guard,
        r11_product_shadow_trial,
        r12_product_support_gate,
    )
    customer_sections = list(R6_PRODUCT_CUSTOMER_VALUE_SECTIONS)
    if r8_robustness_holdout_gate is not None:
        customer_sections.insert(-2, "r8_method_support")
    if r9_holdout_guard is not None:
        customer_sections.insert(-2, "r9_method_support")
    if r11_product_shadow_trial is not None:
        customer_sections.insert(-2, "r11_shadow_trial")
    if r12_product_support_gate is not None:
        customer_sections.insert(-2, "r12_transfer_evidence")
    report = {
        "schema_version": R6_PRODUCT_CUSTOMER_VALUE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "customer_value_report_ready_guarded",
        "positioning": "人群反应趋势与风险区间模拟器",
        "customer_sections": customer_sections,
        "report_contract": {
            "source_backed_only": True,
            "static_narrative_fallback_allowed": False,
            "precise_point_prediction_allowed": False,
            "customer_facing_ui_demo_ready": frontend_demo_ready,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "display_payload": _display_payload(
            metrics,
            support,
            counterfactual,
            counterfactual_holdout,
            r8_robustness_holdout_gate,
            r8_stop_loss_diagnosis,
            r8_product_failure_diagnosis_package,
            r9_combination_comparison,
            r9_synthetic_mechanism_lab,
            r9_false_alarm_gate_redesign,
            r9_holdout_guard,
            r11_product_shadow_trial,
            r12_product_support_gate,
        ),
        "section_contracts": _section_contracts(
            decision,
            metrics,
            support,
            counterfactual,
            counterfactual_holdout,
            r8_robustness_holdout_gate,
            r8_stop_loss_diagnosis,
            r8_product_failure_diagnosis_package,
            r9_combination_comparison,
            r9_synthetic_mechanism_lab,
            r9_false_alarm_gate_redesign,
            r9_holdout_guard,
            r11_product_shadow_trial,
            r12_product_support_gate,
        ),
        "source_registry": source_registry,
        "source_refs": [entry["artifact_id"] for entry in source_registry],
        "blocked_claims": _unique_strings(
            [
                *decision.get("blocked_claims", []),
                *support.get("blocked_claims", []),
                *(r8_robustness_holdout_gate or {}).get("blocked_claims", []),
                *(r8_stop_loss_diagnosis or {}).get("blocked_claims", []),
                *(r8_product_failure_diagnosis_package or {}).get(
                    "blocked_claims",
                    [],
                ),
                *(r9_combination_comparison or {}).get("blocked_claims", []),
                *(r9_synthetic_mechanism_lab or {}).get("blocked_claims", []),
                *(r9_false_alarm_gate_redesign or {}).get("blocked_claims", []),
                *(r9_holdout_guard or {}).get("blocked_claims", []),
                *(r11_product_shadow_trial or {}).get("blocked_claims", []),
                *(r12_product_support_gate or {}).get("blocked_claims", []),
                "精准预测系统",
                "系统可以精确预测单点结果",
            ]
        ),
        "allowed_claims": [
            (
                "Product can display trend, interval, distribution, abnormal "
                "segments, and mechanism explanation from source-backed artifacts."
            ),
            (
                "Current output is guarded and does not claim field validation or "
                "precise point prediction."
            ),
        ],
        "blocking_gaps": _blocking_gaps(frontend_demo_ready),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_customer_value_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_customer_value_report(**kwargs))


def _display_payload(
    metrics: dict[str, Any],
    support: dict[str, Any],
    counterfactual: dict[str, Any],
    counterfactual_holdout: dict[str, Any],
    r8_robustness_holdout_gate: dict[str, Any] | None = None,
    r8_stop_loss_diagnosis: dict[str, Any] | None = None,
    r8_product_failure_diagnosis_package: dict[str, Any] | None = None,
    r9_combination_comparison: dict[str, Any] | None = None,
    r9_synthetic_mechanism_lab: dict[str, Any] | None = None,
    r9_false_alarm_gate_redesign: dict[str, Any] | None = None,
    r9_holdout_guard: dict[str, Any] | None = None,
    r11_product_shadow_trial: dict[str, Any] | None = None,
    r12_product_support_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cases = metrics["case_results"]
    payload = {
        "trend_direction": {
            "summary_metric": metrics["summary"]["trend_direction_accuracy"],
            "support_status": _support_status(support, "trend_direction"),
            "cases": [
                {
                    "source_key": case["source_key"],
                    "trend_direction": case["trend_direction"],
                    "outcome_direction": case["outcome_direction"],
                    "matches_outcome": case["trend_direction_matches_outcome"],
                }
                for case in cases
            ],
        },
        "risk_interval": {
            "summary_metric": metrics["summary"]["interval_coverage"],
            "support_status": _support_status(support, "risk_interval"),
            "cases": [
                {
                    "source_key": case["source_key"],
                    "risk_interval": case["risk_interval"],
                    "observed_reject_proxy": case["observed_reject_proxy"],
                }
                for case in cases
            ],
        },
        "risk_distribution": {
            "risk_ranking_quality": metrics["summary"]["risk_ranking_quality"],
            "false_alarm_rate": metrics["summary"]["false_alarm_rate"],
            "support_status": _support_status(support, "risk_distribution"),
        },
        "abnormal_segments": [
            {
                "source_key": case["source_key"],
                "segments": case["top_abnormal_segments"],
                "support_status": _support_status(support, "abnormal_segments"),
            }
            for case in cases
        ],
        "mechanism_explanation": {
            "support_status": _support_status(support, "mechanism_explanation"),
            "claim_status": "diagnostic_only",
        },
        "counterfactual_policy_comparison": {
            "support_status": _support_status(
                support,
                "counterfactual_policy_comparison",
            ),
            "claim_status": "diagnostic",
            "summary": counterfactual["summary"],
            "holdout_summary": {
                **counterfactual_holdout["summary"],
                "independent_holdout_passed": counterfactual_holdout[
                    "acceptance_gates"
                ]["independent_holdout_passed"],
            },
            "top_policy_by_case": [
                {
                    "source_key": case["source_key"],
                    "top_policy": case["counterfactual_policy_results"][0],
                    "source_artifact_ids": [
                        counterfactual["artifact_id"],
                        counterfactual_holdout["artifact_id"],
                    ],
                }
                for case in counterfactual["case_results"]
            ],
        },
        "research_support": {
            "overall_product_core_value_supported": support[
                "overall_product_core_value_supported"
            ],
            "support_coverage": support.get("support_coverage", {}),
            "product_claim_support_summary": support.get(
                "product_claim_support_summary",
                {},
            ),
            "research_next_task_execution_summary": support.get(
                "research_next_task_execution_summary",
                {},
            ),
            "support_gap_ledger": support.get(
                "support_gap_ledger",
                _support_gap_ledger_from_matrix(support),
            ),
            "research_next_tasks": support.get("research_next_tasks", []),
        },
    }
    if r8_robustness_holdout_gate is not None:
        source_artifact_ids = [r8_robustness_holdout_gate["artifact_id"]]
        if r8_stop_loss_diagnosis is not None:
            source_artifact_ids.append(r8_stop_loss_diagnosis["artifact_id"])
        if r8_product_failure_diagnosis_package is not None:
            source_artifact_ids.append(
                r8_product_failure_diagnosis_package["artifact_id"]
            )
        payload["r8_method_support"] = {
            "status": r8_robustness_holdout_gate["status"],
            "l1_status": r8_robustness_holdout_gate["l1_status"],
            "l2_status": r8_robustness_holdout_gate["l2_status"],
            "stop_loss_recommendation": r8_robustness_holdout_gate[
                "stop_loss_recommendation"
            ],
            "field_outcome_validated": r8_robustness_holdout_gate[
                "acceptance_gates"
            ]["field_outcome_validated"],
            "runtime_default_allowed": r8_robustness_holdout_gate[
                "acceptance_gates"
            ]["runtime_default_allowed"],
            "source_artifact_ids": source_artifact_ids,
        }
        if r8_stop_loss_diagnosis is not None:
            payload["r8_method_support"].update(
                {
                    "diagnosis_status": r8_stop_loss_diagnosis["status"],
                    "research_decision": r8_stop_loss_diagnosis[
                        "research_decision"
                    ],
                    "root_causes": r8_stop_loss_diagnosis["root_causes"],
                    "recommended_next_tracks": r8_stop_loss_diagnosis[
                        "recommended_next_tracks"
                    ],
                }
            )
        if r8_product_failure_diagnosis_package is not None:
            payload["r8_method_support"].update(
                {
                    "failure_diagnosis_package_status": (
                        r8_product_failure_diagnosis_package["status"]
                    ),
                    "failure_cards": r8_product_failure_diagnosis_package[
                        "failure_cards"
                    ],
                    "evidence_requests": r8_product_failure_diagnosis_package[
                        "evidence_requests"
                    ],
                    "outcome_replay_workflow": (
                        r8_product_failure_diagnosis_package[
                            "outcome_replay_workflow"
                        ]
                    ),
                }
            )
    if r9_holdout_guard is not None:
        source_artifact_ids = []
        for artifact in [
            r9_combination_comparison,
            r9_synthetic_mechanism_lab,
            r9_false_alarm_gate_redesign,
            r9_holdout_guard,
        ]:
            if artifact is not None:
                source_artifact_ids.append(artifact["artifact_id"])
        comparison_signal = (
            r9_combination_comparison.get("r9_success_signal", {})
            if r9_combination_comparison is not None
            else {}
        )
        payload["r9_method_support"] = {
            "support_status": "guarded_diagnostic_candidate",
            "best_combination_id": comparison_signal.get("best_combination_id"),
            "metrics_beating_r7_v2": comparison_signal.get(
                "metrics_beating_r7_v2",
                [],
            ),
            "combination_comparison_status": (
                r9_combination_comparison["status"]
                if r9_combination_comparison is not None
                else None
            ),
            "holdout_guard_status": r9_holdout_guard["status"],
            "false_alarm_gate_status": (
                r9_false_alarm_gate_redesign["status"]
                if r9_false_alarm_gate_redesign is not None
                else None
            ),
            "synthetic_mechanism_recovery_passed": (
                r9_synthetic_mechanism_lab["summary"][
                    "synthetic_mechanism_recovery_passed"
                ]
                if r9_synthetic_mechanism_lab is not None
                else None
            ),
            "holdout_summary": r9_holdout_guard["summary"],
            "false_alarm_gate_summary": r9_holdout_guard.get(
                "false_alarm_gate_summary"
            ),
            "research_decision": r9_holdout_guard["research_decision"],
            "product_decision": r9_holdout_guard["product_decision"],
            "field_outcome_validated": r9_holdout_guard["acceptance_gates"][
                "field_outcome_validated"
            ],
            "runtime_default_allowed": r9_holdout_guard["acceptance_gates"][
                "runtime_default_allowed"
            ],
            "blocked_claims": r9_holdout_guard["blocked_claims"],
            "source_artifact_ids": source_artifact_ids,
        }
    if r11_product_shadow_trial is not None:
        evidence_card = r11_product_shadow_trial["shadow_evidence_card"]
        primary = r11_product_shadow_trial["customer_visible_primary_decision"]
        payload["r11_shadow_trial"] = {
            "support_status": evidence_card["claim_status"],
            "trial_status": r11_product_shadow_trial["status"],
            "claim_level": r11_product_shadow_trial["claim_level"],
            "metrics": evidence_card["metrics"],
            "evidence_summary": evidence_card["evidence_summary"],
            "primary_decision_source": primary["primary_decision_source"],
            "r11_shadow_output_role": primary["r11_shadow_output_role"],
            "r11_can_override_primary_decision": primary[
                "r11_can_override_primary_decision"
            ],
            "field_outcome_validated": r11_product_shadow_trial["acceptance_gates"][
                "field_outcome_validated"
            ],
            "runtime_default_allowed": r11_product_shadow_trial["acceptance_gates"][
                "runtime_default_allowed"
            ],
            "outcome_review_handoff": r11_product_shadow_trial[
                "outcome_review_handoff"
            ],
            "blocked_claims": r11_product_shadow_trial["blocked_claims"],
            "source_artifact_ids": [r11_product_shadow_trial["artifact_id"]],
        }
    if r12_product_support_gate is not None:
        evidence_card = r12_product_support_gate["transfer_evidence_card"]
        primary = r12_product_support_gate["customer_visible_primary_decision"]
        payload["r12_transfer_evidence"] = {
            "support_status": evidence_card["claim_status"],
            "gate_status": r12_product_support_gate["status"],
            "claim_level": r12_product_support_gate["claim_level"],
            "metrics": evidence_card["metrics"],
            "evidence_summary": evidence_card["evidence_summary"],
            "primary_decision_source": primary["primary_decision_source"],
            "r12_output_role": primary["r12_output_role"],
            "r12_can_override_primary_decision": primary[
                "r12_can_override_primary_decision"
            ],
            **(
                {
                    "public_data_validation_scope": r12_product_support_gate[
                        "public_data_validation_scope"
                    ],
                    "public_data_effectiveness_claim_allowed": (
                        r12_product_support_gate["acceptance_gates"][
                            "r12_public_data_effectiveness_claim_allowed"
                        ]
                    ),
                    "customer_field_validation_required_for_current_stage": (
                        r12_product_support_gate["acceptance_gates"][
                            "customer_field_validation_required_for_current_stage"
                        ]
                    ),
                }
                if "public_data_validation_scope" in r12_product_support_gate
                else {}
            ),
            "field_outcome_validated": r12_product_support_gate["acceptance_gates"][
                "field_outcome_validated"
            ],
            "runtime_default_allowed": r12_product_support_gate["acceptance_gates"][
                "runtime_default_allowed"
            ],
            "outcome_review_handoff": r12_product_support_gate[
                "outcome_review_handoff"
            ],
            "blocked_claims": r12_product_support_gate["blocked_claims"],
            "source_artifact_ids": [r12_product_support_gate["artifact_id"]],
        }
    return payload


def _section_contracts(
    decision: dict[str, Any],
    metrics: dict[str, Any],
    support: dict[str, Any],
    counterfactual: dict[str, Any],
    counterfactual_holdout: dict[str, Any],
    r8_robustness_holdout_gate: dict[str, Any] | None = None,
    r8_stop_loss_diagnosis: dict[str, Any] | None = None,
    r8_product_failure_diagnosis_package: dict[str, Any] | None = None,
    r9_combination_comparison: dict[str, Any] | None = None,
    r9_synthetic_mechanism_lab: dict[str, Any] | None = None,
    r9_false_alarm_gate_redesign: dict[str, Any] | None = None,
    r9_holdout_guard: dict[str, Any] | None = None,
    r11_product_shadow_trial: dict[str, Any] | None = None,
    r12_product_support_gate: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    contracts = [
        {
            "section_id": "static_prior_baseline",
            "source_artifact_ids": [decision["artifact_id"]],
        },
        {
            "section_id": "trend_direction",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "risk_interval",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "risk_distribution",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "abnormal_segments",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "mechanism_explanation",
            "source_artifact_ids": [support["artifact_id"]],
        },
        {
            "section_id": "counterfactual_policy_comparison",
            "source_artifact_ids": [
                support["artifact_id"],
                counterfactual["artifact_id"],
                counterfactual_holdout["artifact_id"],
            ],
        },
        {
            "section_id": "research_support_gap_ledger",
            "source_artifact_ids": [support["artifact_id"]],
        },
        {
            "section_id": "evidence_and_blocked_claims",
            "source_artifact_ids": [decision["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "outcome_review_plan",
            "source_artifact_ids": [decision["artifact_id"]],
        },
    ]
    if r8_robustness_holdout_gate is not None:
        source_artifact_ids = [r8_robustness_holdout_gate["artifact_id"]]
        if r8_stop_loss_diagnosis is not None:
            source_artifact_ids.append(r8_stop_loss_diagnosis["artifact_id"])
        if r8_product_failure_diagnosis_package is not None:
            source_artifact_ids.append(
                r8_product_failure_diagnosis_package["artifact_id"]
            )
        contracts.insert(
            -2,
            {
                "section_id": "r8_method_support",
                "claim_status": (
                    "guarded"
                    if r8_robustness_holdout_gate["l1_status"] == "passed_guarded"
                    else "diagnostic"
                ),
                "source_artifact_ids": source_artifact_ids,
                "blocked_claims": _unique_strings(
                    [
                        *r8_robustness_holdout_gate["blocked_claims"],
                        *(r8_stop_loss_diagnosis or {}).get("blocked_claims", []),
                        *(r8_product_failure_diagnosis_package or {}).get(
                            "blocked_claims",
                            [],
                        ),
                    ]
                ),
            },
        )
    if r9_holdout_guard is not None:
        source_artifact_ids = [
            artifact["artifact_id"]
            for artifact in [
                r9_combination_comparison,
                r9_synthetic_mechanism_lab,
                r9_false_alarm_gate_redesign,
                r9_holdout_guard,
            ]
            if artifact is not None
        ]
        contracts.insert(
            -2,
            {
                "section_id": "r9_method_support",
                "claim_status": "guarded_diagnostic",
                "source_artifact_ids": source_artifact_ids,
                "blocked_claims": _unique_strings(
                    [
                        *(r9_combination_comparison or {}).get(
                            "blocked_claims",
                            [],
                        ),
                        *(r9_synthetic_mechanism_lab or {}).get(
                            "blocked_claims",
                            [],
                        ),
                        *(r9_false_alarm_gate_redesign or {}).get(
                            "blocked_claims",
                            [],
                        ),
                        *r9_holdout_guard["blocked_claims"],
                    ]
                ),
            },
        )
    if r11_product_shadow_trial is not None:
        contracts.insert(
            -2,
            {
                "section_id": "r11_shadow_trial",
                "claim_status": "shadow_only",
                "source_artifact_ids": [r11_product_shadow_trial["artifact_id"]],
                "blocked_claims": r11_product_shadow_trial["blocked_claims"],
            },
        )
    if r12_product_support_gate is not None:
        contracts.insert(
            -2,
            {
                "section_id": "r12_transfer_evidence",
                "claim_status": "secondary_evidence_only",
                "source_artifact_ids": [r12_product_support_gate["artifact_id"]],
                "blocked_claims": r12_product_support_gate["blocked_claims"],
            },
        )
    return contracts


def _source_registry(
    decision: dict[str, Any],
    metrics: dict[str, Any],
    support: dict[str, Any],
    counterfactual: dict[str, Any],
    counterfactual_holdout: dict[str, Any],
    r8_robustness_holdout_gate: dict[str, Any] | None = None,
    r8_stop_loss_diagnosis: dict[str, Any] | None = None,
    r8_product_failure_diagnosis_package: dict[str, Any] | None = None,
    r9_combination_comparison: dict[str, Any] | None = None,
    r9_synthetic_mechanism_lab: dict[str, Any] | None = None,
    r9_false_alarm_gate_redesign: dict[str, Any] | None = None,
    r9_holdout_guard: dict[str, Any] | None = None,
    r11_product_shadow_trial: dict[str, Any] | None = None,
    r12_product_support_gate: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    support_path = (
        "experiments/results/r6_research_product_value_support_v2/"
        "r6-research-product-value-support-v2-current-001.json"
        if support.get("schema_version") == "r6-research-product-value-support-v2"
        else (
            "experiments/results/r6_research_product_value_support/"
            "r6-research-product-value-support-current-001.json"
        )
    )
    registry = [
        {
            "artifact_id": decision["artifact_id"],
            "path": (
                "experiments/results/r6_product_decision_report/"
                "r6-product-decision-report-current-001.json"
            ),
        },
        {
            "artifact_id": metrics["artifact_id"],
            "path": (
                "experiments/results/r6_trend_interval_risk_metrics/"
                "r6-trend-interval-risk-metrics-current-001.json"
            ),
        },
        {
            "artifact_id": support["artifact_id"],
            "path": support_path,
        },
        {
            "artifact_id": "r6-product-claim-evidence-registry-current-001",
            "path": (
                "experiments/results/r6_product_claim_evidence_registry/"
                "r6-product-claim-evidence-registry-current-001.json"
            ),
        },
        {
            "artifact_id": counterfactual["artifact_id"],
            "path": (
                "experiments/results/r6_learning_counterfactual_simulator/"
                "r6-learning-counterfactual-simulator-current-001.json"
            ),
        },
        {
            "artifact_id": counterfactual_holdout["artifact_id"],
            "path": (
                "experiments/results/r6_learning_counterfactual_holdout_validation/"
                "r6-learning-counterfactual-holdout-validation-current-001.json"
            ),
        },
    ]
    if r8_robustness_holdout_gate is not None:
        registry.append(
            {
                "artifact_id": r8_robustness_holdout_gate["artifact_id"],
                "path": (
                    "experiments/results/r8_robustness_holdout_gate/"
                    "r8-robustness-holdout-gate-current-001.json"
                ),
            }
        )
    if r8_stop_loss_diagnosis is not None:
        registry.append(
            {
                "artifact_id": r8_stop_loss_diagnosis["artifact_id"],
                "path": (
                    "experiments/results/r8_stop_loss_diagnosis/"
                    "r8-stop-loss-diagnosis-current-001.json"
                ),
            }
        )
    if r8_product_failure_diagnosis_package is not None:
        registry.append(
            {
                "artifact_id": r8_product_failure_diagnosis_package["artifact_id"],
                "path": (
                    "experiments/results/r8_product_failure_diagnosis_package/"
                    "r8-product-failure-diagnosis-package-current-001.json"
                ),
            }
        )
    if r9_combination_comparison is not None:
        registry.append(
            {
                "artifact_id": r9_combination_comparison["artifact_id"],
                "path": (
                    "experiments/results/r9_combination_comparison/"
                    "r9-combination-comparison-current-001.json"
                ),
            }
        )
    if r9_synthetic_mechanism_lab is not None:
        registry.append(
            {
                "artifact_id": r9_synthetic_mechanism_lab["artifact_id"],
                "path": (
                    "experiments/results/r9_synthetic_mechanism_lab/"
                    "r9-synthetic-mechanism-lab-current-001.json"
                ),
            }
        )
    if r9_false_alarm_gate_redesign is not None:
        registry.append(
            {
                "artifact_id": r9_false_alarm_gate_redesign["artifact_id"],
                "path": (
                    "experiments/results/r9_false_alarm_gate_redesign/"
                    "r9-false-alarm-gate-redesign-current-001.json"
                ),
            }
        )
    if r9_holdout_guard is not None:
        registry.append(
            {
                "artifact_id": r9_holdout_guard["artifact_id"],
                "path": (
                    "experiments/results/r9_holdout_guard/"
                    "r9-holdout-guard-current-001.json"
                ),
            }
        )
    if r11_product_shadow_trial is not None:
        registry.append(
            {
                "artifact_id": r11_product_shadow_trial["artifact_id"],
                "path": (
                    "experiments/results/r11_product_shadow_trial/"
                    "r11-product-shadow-trial-current-001.json"
                ),
            }
        )
        registry.extend(r11_product_shadow_trial.get("source_registry", []))
    if r12_product_support_gate is not None:
        registry.append(
            {
                "artifact_id": r12_product_support_gate["artifact_id"],
                "path": (
                    "experiments/results/r12_product_support_gate/"
                    "r12-product-support-gate-current-001.json"
                ),
            }
        )
        registry.extend(r12_product_support_gate.get("source_registry", []))
    return registry


def _support_status(support: dict[str, Any], product_value: str) -> str:
    for item in support["support_matrix"]:
        if item["product_value"] == product_value:
            return item["support_status"]
    raise ValueError(f"missing support_matrix item: {product_value}")


def _support_gap_ledger_from_matrix(support: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "product_value": item["product_value"],
            "current_support_status": item["support_status"],
            "product_display_level": item["claim_status"],
            "blocking_gap_ids": [item["blocked_reason"]]
            if item.get("blocked_reason")
            else [],
            "source_artifact_ids": item["source_artifact_ids"],
        }
        for item in support.get("support_matrix", [])
    ]


def _unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _frontend_demo_ready() -> bool:
    repo_root = Path(__file__).resolve().parents[1]
    required_files = [
        repo_root / "demo" / "index.html",
        repo_root / "demo" / "app.js",
        repo_root / "demo" / "styles.css",
    ]
    return all(path.is_file() for path in required_files)


def _blocking_gaps(frontend_demo_ready: bool) -> list[str]:
    gaps = [
        "needs_field_outcome_validation",
        "needs_runtime_default_holdout_review",
    ]
    if frontend_demo_ready:
        gaps.append("needs_customer_workflow_runtime_integration")
    else:
        gaps.insert(0, "needs_customer_facing_ui_integration")
    return gaps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--r8-robustness-holdout-gate-path", default=None)
    parser.add_argument("--r8-stop-loss-diagnosis-path", default=None)
    parser.add_argument("--r8-product-failure-diagnosis-package-path", default=None)
    parser.add_argument("--r9-combination-comparison-path", default=None)
    parser.add_argument("--r9-synthetic-mechanism-lab-path", default=None)
    parser.add_argument("--r9-false-alarm-gate-redesign-path", default=None)
    parser.add_argument("--r9-holdout-guard-path", default=None)
    parser.add_argument("--r11-product-shadow-trial-path", default=None)
    parser.add_argument("--r12-product-support-gate-path", default=None)
    args = parser.parse_args()
    r8_gate = (
        load_json_artifact(args.r8_robustness_holdout_gate_path)
        if args.r8_robustness_holdout_gate_path
        else None
    )
    r8_diagnosis = (
        load_json_artifact(args.r8_stop_loss_diagnosis_path)
        if args.r8_stop_loss_diagnosis_path
        else None
    )
    r8_failure_package = (
        load_json_artifact(args.r8_product_failure_diagnosis_package_path)
        if args.r8_product_failure_diagnosis_package_path
        else None
    )
    r9_comparison = (
        load_json_artifact(args.r9_combination_comparison_path)
        if args.r9_combination_comparison_path
        else None
    )
    r9_synthetic_lab = (
        load_json_artifact(args.r9_synthetic_mechanism_lab_path)
        if args.r9_synthetic_mechanism_lab_path
        else None
    )
    r9_false_alarm_gate = (
        load_json_artifact(args.r9_false_alarm_gate_redesign_path)
        if args.r9_false_alarm_gate_redesign_path
        else None
    )
    r9_holdout_guard = (
        load_json_artifact(args.r9_holdout_guard_path)
        if args.r9_holdout_guard_path
        else None
    )
    r11_shadow_trial = (
        load_json_artifact(args.r11_product_shadow_trial_path)
        if args.r11_product_shadow_trial_path
        else None
    )
    r12_support_gate = (
        load_json_artifact(args.r12_product_support_gate_path)
        if args.r12_product_support_gate_path
        else None
    )

    output_path = write_r6_product_customer_value_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r8_robustness_holdout_gate=r8_gate,
        r8_stop_loss_diagnosis=r8_diagnosis,
        r8_product_failure_diagnosis_package=r8_failure_package,
        r9_combination_comparison=r9_comparison,
        r9_synthetic_mechanism_lab=r9_synthetic_lab,
        r9_false_alarm_gate_redesign=r9_false_alarm_gate,
        r9_holdout_guard=r9_holdout_guard,
        r11_product_shadow_trial=r11_shadow_trial,
        r12_product_support_gate=r12_support_gate,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output_path),
                "status": report["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
