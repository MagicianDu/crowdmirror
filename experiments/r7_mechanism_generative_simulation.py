from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact


R7_CLAIM_BOUNDARY = (
    "R7 contract-first artifact. It supports mechanism-generative interaction "
    "risk simulation, trend interval diagnosis, segment anomaly analysis, "
    "counterfactual policy sandboxing, and outcome-feedback learning only; it "
    "is not point-prediction evidence, not field validation, and not runtime "
    "default authorization."
)

R7_BUNDLE_SCHEMA_VERSION = "r7-mechanism-generative-bundle-v1"
R7_MECHANISM_STATE_MANIFEST_SCHEMA_VERSION = "r7-mechanism-state-manifest-v1"
R7_INTERACTION_GRAPH_MANIFEST_SCHEMA_VERSION = "r7-interaction-graph-manifest-v1"
R7_ROLLOUT_DISTRIBUTION_SCHEMA_VERSION = "r7-rollout-distribution-v1"
R7_RISK_INTERVAL_REPORT_SCHEMA_VERSION = "r7-risk-interval-report-v1"
R7_SEGMENT_ANOMALY_REPORT_SCHEMA_VERSION = "r7-segment-anomaly-report-v1"
R7_COUNTERFACTUAL_POLICY_SANDBOX_SCHEMA_VERSION = "r7-counterfactual-policy-sandbox-v1"
R7_OUTCOME_FEEDBACK_UPDATE_CANDIDATE_SCHEMA_VERSION = (
    "r7-outcome-feedback-update-candidate-v1"
)
R7_PRODUCT_SUPPORT_REPORT_SCHEMA_VERSION = "r7-product-support-report-v1"

MECHANISM_DIMENSIONS = [
    "price_sensitivity",
    "trust_loss",
    "fairness_perception",
    "substitution_option",
    "identity_alignment",
    "social_diffusion_sensitivity",
]

PRODUCT_OUTPUTS = [
    "trend_direction",
    "risk_interval",
    "risk_distribution",
    "abnormal_segments",
    "mechanism_explanation",
    "counterfactual_policy_sandbox",
]


def build_r7_mechanism_generative_bundle(
    *,
    artifact_id: str,
    run_id: str,
    case_id: str = "generic-price-change",
    rollout_count: int = 50,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    case_id = non_empty_string(case_id, field="case_id")
    case = get_r6_case_template(case_id)

    mechanism_state = build_r7_mechanism_state_manifest(
        artifact_id=f"{artifact_id}-mechanism-state",
        run_id=run_id,
        case=case,
    )
    interaction_graph = build_r7_interaction_graph_manifest(
        artifact_id=f"{artifact_id}-interaction-graph",
        run_id=run_id,
        case=case,
        mechanism_state=mechanism_state,
    )
    rollout_distribution = build_r7_rollout_distribution(
        artifact_id=f"{artifact_id}-rollout-distribution",
        run_id=run_id,
        mechanism_state=mechanism_state,
        interaction_graph=interaction_graph,
        rollout_count=rollout_count,
    )
    risk_interval = build_r7_risk_interval_report(
        artifact_id=f"{artifact_id}-risk-interval",
        run_id=run_id,
        rollout_distribution=rollout_distribution,
    )
    segment_anomaly = build_r7_segment_anomaly_report(
        artifact_id=f"{artifact_id}-segment-anomaly",
        run_id=run_id,
        mechanism_state=mechanism_state,
        rollout_distribution=rollout_distribution,
        case=case,
    )
    policy_sandbox = build_r7_counterfactual_policy_sandbox(
        artifact_id=f"{artifact_id}-policy-sandbox",
        run_id=run_id,
        risk_interval=risk_interval,
        rollout_distribution=rollout_distribution,
    )
    outcome_update = build_r7_outcome_feedback_update_candidate(
        artifact_id=f"{artifact_id}-outcome-feedback-update",
        run_id=run_id,
        risk_interval=risk_interval,
        segment_anomaly=segment_anomaly,
        case=case,
    )
    product_support = build_r7_product_support_report(
        artifact_id=f"{artifact_id}-product-support",
        run_id=run_id,
        mechanism_state=mechanism_state,
        interaction_graph=interaction_graph,
        rollout_distribution=rollout_distribution,
        risk_interval=risk_interval,
        segment_anomaly=segment_anomaly,
        policy_sandbox=policy_sandbox,
        outcome_update=outcome_update,
    )

    artifacts = {
        "r7_mechanism_state_manifest": mechanism_state,
        "r7_interaction_graph_manifest": interaction_graph,
        "r7_rollout_distribution": rollout_distribution,
        "r7_risk_interval_report": risk_interval,
        "r7_segment_anomaly_report": segment_anomaly,
        "r7_counterfactual_policy_sandbox": policy_sandbox,
        "r7_outcome_feedback_update_candidate": outcome_update,
        "r7_product_support_report": product_support,
    }
    payload = {
        "schema_version": R7_BUNDLE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "case_id": case_id,
        "status": "r7_contract_first_mvp_ready_guarded",
        "claim_boundary": R7_CLAIM_BOUNDARY,
        "source_refs": [
            case["case_id"],
            case["scenario"]["scenario_id"],
            *case["scenario"]["source_refs"],
        ],
        "artifacts": artifacts,
        "acceptance_gates": {
            "artifact_contracts_present": True,
            "product_six_outputs_source_backed": True,
            "interaction_trace_present": True,
            "rollout_distribution_present": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            "R7 contract-first mechanism process is source-backed and replayable.",
            "R7 can be shown as guarded trend, interval, segment, and policy sandbox evidence.",
            "R6 remains a guard and diagnostic baseline, not the active main method.",
        ],
        "blocked_claims": [
            "精准预测系统",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "interaction simulation is always more accurate than static prior",
        ],
    }
    assert_strict_json(payload)
    return payload


def build_r7_mechanism_state_manifest(
    *,
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    segment_states = []
    for segment in case["prior_segments"]:
        traits = segment["static_traits"]
        mechanism_state = _mechanism_state_for_segment(
            traits=traits,
            impact_dimensions=case["scenario"]["impact_dimensions"],
            change_type=case["scenario"]["change_type"],
        )
        segment_states.append(
            {
                "segment_id": segment["segment_id"],
                "weight": segment["weight"],
                "prior_reject_probability": segment["static_response_prior"]["reject"],
                "static_traits": traits,
                "exposure_state": {
                    "change_type": case["scenario"]["change_type"],
                    "impact_dimensions": case["scenario"]["impact_dimensions"],
                    "shock_intensity": round(sum(mechanism_state.values()) / len(MECHANISM_DIMENSIONS), 4),
                },
                "mechanism_state": mechanism_state,
                "mechanism_sources": {
                    dimension: "rule:scenario_impact_x_static_trait"
                    for dimension in MECHANISM_DIMENSIONS
                },
                "uncertainty_state": {
                    "prior_uncertainty": segment["uncertainty"],
                    "mechanism_uncertainty": round(0.06 + segment["uncertainty"] * 0.35, 4),
                    "propagation_uncertainty": round(
                        0.04 + mechanism_state["social_diffusion_sensitivity"] * 0.08,
                        4,
                    ),
                    "outcome_proxy_uncertainty": 0.08,
                },
                "ablation_ready": True,
                "source_refs": [
                    *segment["source_refs"],
                    case["scenario"]["scenario_id"],
                ],
            }
        )

    payload = _artifact(
        schema_version=R7_MECHANISM_STATE_MANIFEST_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[case["case_id"], case["scenario"]["scenario_id"]],
        body={
            "case_id": case["case_id"],
            "mechanism_dimensions": MECHANISM_DIMENSIONS,
            "segment_mechanism_states": segment_states,
        },
    )
    return payload


def build_r7_interaction_graph_manifest(
    *,
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
    mechanism_state: dict[str, Any],
) -> dict[str, Any]:
    nodes = []
    for segment in mechanism_state["segment_mechanism_states"]:
        nodes.append(
            {
                "node_id": segment["segment_id"],
                "weight": segment["weight"],
                "prior_reject_probability": segment["prior_reject_probability"],
                "diffusion_sensitivity": segment["mechanism_state"][
                    "social_diffusion_sensitivity"
                ],
                "source_refs": segment["source_refs"],
            }
        )

    edges = []
    for source in mechanism_state["segment_mechanism_states"]:
        for target in mechanism_state["segment_mechanism_states"]:
            if source["segment_id"] == target["segment_id"]:
                continue
            shared_pressure = _shared_mechanism_pressure(
                source["mechanism_state"],
                target["mechanism_state"],
            )
            edges.append(
                {
                    "source": source["segment_id"],
                    "target": target["segment_id"],
                    "relationship_type": "mechanism_similarity_and_peer_exposure",
                    "strength": round(0.08 + shared_pressure * 0.22, 4),
                    "source_refs": [source["segment_id"], target["segment_id"]],
                }
            )

    payload = _artifact(
        schema_version=R7_INTERACTION_GRAPH_MANIFEST_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[mechanism_state["artifact_id"], case["case_id"]],
        body={
            "case_id": case["case_id"],
            "nodes": nodes,
            "edges": edges,
            "controls": {
                "no_interaction_control_present": True,
                "interaction_on_present": True,
            },
            "propagation_steps": [
                {
                    "step": 0,
                    "operator": "initialize_from_static_prior_and_mechanism_activation",
                },
                {
                    "step": 1,
                    "operator": "propagate_peer_exposure_by_edge_strength",
                },
                {
                    "step": 2,
                    "operator": "stabilize_with_prior_anchor_and_guarded_uncertainty",
                },
            ],
        },
    )
    return payload


def build_r7_rollout_distribution(
    *,
    artifact_id: str,
    run_id: str,
    mechanism_state: dict[str, Any],
    interaction_graph: dict[str, Any],
    rollout_count: int = 50,
) -> dict[str, Any]:
    if rollout_count < 1:
        raise ValueError("rollout_count must be positive")
    rollouts = [
        _build_single_rollout(
            seed=seed,
            mechanism_state=mechanism_state,
            interaction_graph=interaction_graph,
        )
        for seed in range(rollout_count)
    ]
    no_interaction_values = [
        rollout["aggregate"]["no_interaction"] for rollout in rollouts
    ]
    interaction_values = [
        rollout["aggregate"]["interaction_on"] for rollout in rollouts
    ]

    payload = _artifact(
        schema_version=R7_ROLLOUT_DISTRIBUTION_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[mechanism_state["artifact_id"], interaction_graph["artifact_id"]],
        body={
            "rollout_count": rollout_count,
            "seeded_reproducible": True,
            "rollouts": rollouts,
            "no_interaction_control": _distribution_summary(no_interaction_values),
            "interaction_on": _distribution_summary(interaction_values),
            "uncertainty_sources": [
                "static_prior_uncertainty",
                "mechanism_activation_uncertainty",
                "propagation_strength_uncertainty",
                "outcome_proxy_uncertainty",
            ],
        },
    )
    return payload


def build_r7_risk_interval_report(
    *,
    artifact_id: str,
    run_id: str,
    rollout_distribution: dict[str, Any],
) -> dict[str, Any]:
    interaction = rollout_distribution["interaction_on"]
    interval_width = round(interaction["p90"] - interaction["p10"], 4)
    payload = _artifact(
        schema_version=R7_RISK_INTERVAL_REPORT_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout_distribution["artifact_id"]],
        body={
            "trend_direction": (
                "risk_increase"
                if interaction["median"]
                > rollout_distribution["no_interaction_control"]["median"]
                else "risk_flat_or_decrease"
            ),
            "risk_interval": {
                "p10": interaction["p10"],
                "median": interaction["median"],
                "p90": interaction["p90"],
                "interval_width": interval_width,
                "over_wide_penalty": round(max(0.0, interval_width - 0.18), 4),
            },
            "coverage_status": "current_proxy_interval_diagnostic",
            "claim_status": "guarded",
        },
    )
    return payload


def build_r7_segment_anomaly_report(
    *,
    artifact_id: str,
    run_id: str,
    mechanism_state: dict[str, Any],
    rollout_distribution: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    segment_medians = _segment_medians(rollout_distribution)
    static_hidden_risks = []
    interaction_amplified_risks = []
    for segment in mechanism_state["segment_mechanism_states"]:
        segment_id = segment["segment_id"]
        medians = segment_medians[segment_id]
        if segment["prior_reject_probability"] < 0.40 and medians["interaction_on"] >= 0.40:
            static_hidden_risks.append(
                {
                    "segment_id": segment_id,
                    "prior_reject_probability": segment["prior_reject_probability"],
                    "interaction_median": medians["interaction_on"],
                    "reason": "static_prior_underestimates_interaction_activated_risk",
                    "source_refs": [mechanism_state["artifact_id"], rollout_distribution["artifact_id"]],
                }
            )
        if medians["interaction_on"] - medians["no_interaction"] >= 0.015:
            interaction_amplified_risks.append(
                {
                    "segment_id": segment_id,
                    "no_interaction_median": medians["no_interaction"],
                    "interaction_median": medians["interaction_on"],
                    "amplification": round(
                        medians["interaction_on"] - medians["no_interaction"],
                        4,
                    ),
                    "source_refs": [rollout_distribution["artifact_id"]],
                }
            )

    observed = case["outcome"]["metrics"]["observed_reject_proxy"]
    predicted = rollout_distribution["interaction_on"]["median"]
    false_alarm_diagnosis = [
        {
            "diagnosis": (
                "aggregate_prediction_near_observed_proxy"
                if predicted <= observed + 0.08
                else "aggregate_prediction_above_observed_proxy_watch"
            ),
            "observed_reject_proxy": observed,
            "interaction_median": predicted,
            "claim_status": "diagnostic",
            "source_refs": [case["outcome"]["release_id"], rollout_distribution["artifact_id"]],
        }
    ]

    payload = _artifact(
        schema_version=R7_SEGMENT_ANOMALY_REPORT_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[mechanism_state["artifact_id"], rollout_distribution["artifact_id"]],
        body={
            "static_hidden_risks": static_hidden_risks,
            "interaction_amplified_risks": interaction_amplified_risks,
            "false_alarm_diagnosis": false_alarm_diagnosis,
            "segment_label_status": "proxy_diagnostic_not_field_segment_label",
        },
    )
    return payload


def build_r7_counterfactual_policy_sandbox(
    *,
    artifact_id: str,
    run_id: str,
    risk_interval: dict[str, Any],
    rollout_distribution: dict[str, Any],
) -> dict[str, Any]:
    base_median = risk_interval["risk_interval"]["median"]
    policy_options = [
        {
            "policy_id": "targeted_compensation",
            "description": "高风险群体补偿或权益缓释",
            "shock_multiplier": 0.72,
            "propagation_multiplier": 0.90,
        },
        {
            "policy_id": "phased_release",
            "description": "分阶段发布，降低一次性冲击",
            "shock_multiplier": 0.82,
            "propagation_multiplier": 0.94,
        },
        {
            "policy_id": "transparent_explanation",
            "description": "强化沟通解释，降低信任损失",
            "shock_multiplier": 0.88,
            "propagation_multiplier": 0.86,
        },
    ]
    policy_results = []
    for option in policy_options:
        median = round(
            base_median
            - (1 - option["shock_multiplier"]) * 0.10
            - (1 - option["propagation_multiplier"]) * 0.06,
            4,
        )
        risk_reduction = round(base_median - median, 4)
        policy_results.append(
            {
                **option,
                "risk_interval": {
                    "p10": round(max(0.0, median - 0.045), 4),
                    "median": median,
                    "p90": round(min(1.0, median + 0.055), 4),
                },
                "risk_reduction_vs_baseline": risk_reduction,
                "dominance_status": (
                    "dominant_on_risk_reduction"
                    if risk_reduction >= 0.025
                    else "trade_off"
                ),
                "source_refs": [risk_interval["artifact_id"], rollout_distribution["artifact_id"]],
            }
        )
    policy_ranking = sorted(
        policy_results,
        key=lambda item: item["risk_reduction_vs_baseline"],
        reverse=True,
    )
    payload = _artifact(
        schema_version=R7_COUNTERFACTUAL_POLICY_SANDBOX_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[risk_interval["artifact_id"], rollout_distribution["artifact_id"]],
        body={
            "baseline_interaction_median": base_median,
            "policy_options": policy_options,
            "policy_results": policy_results,
            "policy_ranking": policy_ranking,
            "claim_status": "guarded_counterfactual_sandbox",
        },
    )
    return payload


def build_r7_outcome_feedback_update_candidate(
    *,
    artifact_id: str,
    run_id: str,
    risk_interval: dict[str, Any],
    segment_anomaly: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    observed = case["outcome"]["metrics"]["observed_reject_proxy"]
    predicted = risk_interval["risk_interval"]["median"]
    error = round(predicted - observed, 4)
    payload = _artifact(
        schema_version=R7_OUTCOME_FEEDBACK_UPDATE_CANDIDATE_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[
            risk_interval["artifact_id"],
            segment_anomaly["artifact_id"],
            case["outcome"]["release_id"],
        ],
        body={
            "observed_reject_proxy": observed,
            "predicted_reject_median": predicted,
            "prediction_error": error,
            "error_attribution": {
                "prior_error": round(abs(error) * 0.25, 4),
                "mechanism_error": round(abs(error) * 0.35, 4),
                "propagation_error": round(abs(error) * 0.25, 4),
                "interval_error": round(abs(error) * 0.15, 4),
            },
            "bounded_update_candidate": {
                "mechanism_learning_rate": 0.15,
                "propagation_learning_rate": 0.08,
                "max_single_update_delta": 0.03,
            },
            "rollback_conditions": [
                "holdout_non_regression_failed",
                "false_alarm_rate_increases",
                "interval_coverage_decreases_without_width_control",
            ],
            "update_status": "blocked_until_holdout_and_runtime_guard",
            "runtime_default_allowed": False,
        },
    )
    return payload


def build_r7_product_support_report(
    *,
    artifact_id: str,
    run_id: str,
    mechanism_state: dict[str, Any],
    interaction_graph: dict[str, Any],
    rollout_distribution: dict[str, Any],
    risk_interval: dict[str, Any],
    segment_anomaly: dict[str, Any],
    policy_sandbox: dict[str, Any],
    outcome_update: dict[str, Any],
) -> dict[str, Any]:
    output_support = [
        {
            "product_output": "trend_direction",
            "claim_status": "guarded",
            "source_artifact_ids": [risk_interval["artifact_id"], rollout_distribution["artifact_id"]],
        },
        {
            "product_output": "risk_interval",
            "claim_status": "guarded",
            "source_artifact_ids": [risk_interval["artifact_id"]],
        },
        {
            "product_output": "risk_distribution",
            "claim_status": "guarded",
            "source_artifact_ids": [rollout_distribution["artifact_id"]],
        },
        {
            "product_output": "abnormal_segments",
            "claim_status": "diagnostic",
            "source_artifact_ids": [segment_anomaly["artifact_id"]],
        },
        {
            "product_output": "mechanism_explanation",
            "claim_status": "guarded",
            "source_artifact_ids": [mechanism_state["artifact_id"], interaction_graph["artifact_id"]],
        },
        {
            "product_output": "counterfactual_policy_sandbox",
            "claim_status": "guarded",
            "source_artifact_ids": [policy_sandbox["artifact_id"]],
        },
    ]
    payload = _artifact(
        schema_version=R7_PRODUCT_SUPPORT_REPORT_SCHEMA_VERSION,
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[
            mechanism_state["artifact_id"],
            interaction_graph["artifact_id"],
            rollout_distribution["artifact_id"],
            risk_interval["artifact_id"],
            segment_anomaly["artifact_id"],
            policy_sandbox["artifact_id"],
            outcome_update["artifact_id"],
        ],
        body={
            "product_positioning": "人群反应趋势与风险区间模拟器",
            "product_outputs": PRODUCT_OUTPUTS,
            "output_support": output_support,
            "support_status": "r7_contract_first_guarded_support",
            "blocked_claims": [
                "精准预测系统",
                "field_outcome_validated=true",
                "runtime_default_allowed=true",
                "accuracy_superiority_over_static_prior",
            ],
        },
    )
    return payload


def _artifact(
    *,
    schema_version: str,
    artifact_id: str,
    run_id: str,
    source_refs: list[str],
    body: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": schema_version,
        "artifact_id": non_empty_string(artifact_id, field="artifact_id"),
        "run_id": non_empty_string(run_id, field="run_id"),
        "source_refs": [non_empty_string(ref, field="source_ref") for ref in source_refs],
        "claim_boundary": R7_CLAIM_BOUNDARY,
        **body,
    }
    assert_strict_json(payload)
    return payload


def _mechanism_state_for_segment(
    *,
    traits: dict[str, str],
    impact_dimensions: list[str],
    change_type: str,
) -> dict[str, float]:
    sensitivity = _trait_score(traits.get("sensitivity"))
    low_trust = 1.0 - _trait_score(traits.get("trust"))
    substitution = _trait_score(traits.get("substitution"))
    impact_text = " ".join(impact_dimensions)
    fairness = 0.75 if "fairness" in impact_text or "equity" in impact_text else 0.35
    rights_or_policy = 0.70 if change_type in {"rule", "policy"} else 0.35
    price = 0.80 if change_type == "price" or "cost" in impact_text else 0.35
    return {
        "price_sensitivity": round(min(1.0, sensitivity * price), 4),
        "trust_loss": round(min(1.0, low_trust * (0.65 + fairness * 0.25)), 4),
        "fairness_perception": round(min(1.0, fairness * (0.55 + sensitivity * 0.35)), 4),
        "substitution_option": round(min(1.0, substitution * 0.85), 4),
        "identity_alignment": round(min(1.0, rights_or_policy * (0.45 + low_trust * 0.30)), 4),
        "social_diffusion_sensitivity": round(
            min(1.0, 0.30 + sensitivity * 0.35 + low_trust * 0.25),
            4,
        ),
    }


def _trait_score(value: str | None) -> float:
    return {"low": 0.20, "medium": 0.55, "high": 0.90}.get(value or "", 0.45)


def _shared_mechanism_pressure(source: dict[str, float], target: dict[str, float]) -> float:
    overlaps = [min(source[dimension], target[dimension]) for dimension in MECHANISM_DIMENSIONS]
    return sum(overlaps) / len(overlaps)


def _build_single_rollout(
    *,
    seed: int,
    mechanism_state: dict[str, Any],
    interaction_graph: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(seed)
    segment_results = []
    edge_strength_by_target: dict[str, float] = {}
    for edge in interaction_graph["edges"]:
        edge_strength_by_target[edge["target"]] = (
            edge_strength_by_target.get(edge["target"], 0.0) + edge["strength"]
        )

    for segment in mechanism_state["segment_mechanism_states"]:
        mechanisms = segment["mechanism_state"]
        mechanism_pressure = sum(mechanisms.values()) / len(MECHANISM_DIMENSIONS)
        prior = segment["prior_reject_probability"]
        uncertainty = segment["uncertainty_state"]
        noise = rng.uniform(-0.006, 0.006)
        no_interaction = _clamp_probability(
            prior
            + 0.025
            + mechanism_pressure * 0.075
            + uncertainty["mechanism_uncertainty"] * 0.08
            + noise
        )
        propagation_delta = (
            mechanisms["social_diffusion_sensitivity"] * 0.030
            + edge_strength_by_target.get(segment["segment_id"], 0.0) * 0.018
        )
        interaction_on = _clamp_probability(no_interaction + propagation_delta)
        segment_results.append(
            {
                "segment_id": segment["segment_id"],
                "weight": segment["weight"],
                "no_interaction": round(no_interaction, 4),
                "interaction_on": round(interaction_on, 4),
                "interaction_delta": round(interaction_on - no_interaction, 4),
            }
        )

    aggregate_no_interaction = sum(
        result["weight"] * result["no_interaction"] for result in segment_results
    )
    aggregate_interaction = sum(
        result["weight"] * result["interaction_on"] for result in segment_results
    )
    return {
        "seed": seed,
        "segment_results": segment_results,
        "aggregate": {
            "no_interaction": round(aggregate_no_interaction, 4),
            "interaction_on": round(aggregate_interaction, 4),
            "interaction_delta": round(
                aggregate_interaction - aggregate_no_interaction,
                4,
            ),
        },
    }


def _distribution_summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "p10": _percentile(ordered, 0.10),
        "median": _percentile(ordered, 0.50),
        "p90": _percentile(ordered, 0.90),
        "mean": round(sum(values) / len(values), 4),
    }


def _percentile(ordered_values: list[float], q: float) -> float:
    if not ordered_values:
        raise ValueError("ordered_values must not be empty")
    position = (len(ordered_values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered_values) - 1)
    fraction = position - lower
    value = ordered_values[lower] * (1 - fraction) + ordered_values[upper] * fraction
    return round(value, 4)


def _segment_medians(rollout_distribution: dict[str, Any]) -> dict[str, dict[str, float]]:
    by_segment: dict[str, dict[str, list[float]]] = {}
    for rollout in rollout_distribution["rollouts"]:
        for segment_result in rollout["segment_results"]:
            segment_id = segment_result["segment_id"]
            by_segment.setdefault(segment_id, {"no_interaction": [], "interaction_on": []})
            by_segment[segment_id]["no_interaction"].append(segment_result["no_interaction"])
            by_segment[segment_id]["interaction_on"].append(segment_result["interaction_on"])
    return {
        segment_id: {
            "no_interaction": _percentile(sorted(values["no_interaction"]), 0.50),
            "interaction_on": _percentile(sorted(values["interaction_on"]), 0.50),
        }
        for segment_id, values in by_segment.items()
    }


def _clamp_probability(value: float) -> float:
    return min(1.0, max(0.0, value))


def write_r7_mechanism_generative_bundle(
    *,
    output: str | Path,
    artifact_id: str,
    run_id: str,
    case_id: str = "generic-price-change",
    rollout_count: int = 50,
) -> Path:
    payload = build_r7_mechanism_generative_bundle(
        artifact_id=artifact_id,
        run_id=run_id,
        case_id=case_id,
        rollout_count=rollout_count,
    )
    return write_json_artifact(output, payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r7-mechanism-generative-bundle-current-001")
    parser.add_argument("--run-id", default="r7-contract-first-current")
    parser.add_argument("--case-id", default="generic-price-change")
    parser.add_argument("--rollout-count", type=int, default=50)
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r7_mechanism_generative_bundle/"
            "r7-mechanism-generative-bundle-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r7_mechanism_generative_bundle(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        case_id=args.case_id,
        rollout_count=args.rollout_count,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output),
                "status": "r7_contract_first_mvp_ready_guarded",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
