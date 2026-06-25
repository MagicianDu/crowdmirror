from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact


R8_CLAIM_BOUNDARY = (
    "R8 learnable mechanism artifact. It supports guarded mechanism-causal "
    "interaction simulation, interval/risk diagnosis, attribution, and bounded "
    "operator update candidates only; it is not point-prediction evidence, not "
    "field validation, and not runtime default authorization."
)
R8_BUNDLE_SCHEMA_VERSION = "r8-learnable-mechanism-bundle-v1"

MECHANISM_CATALOG = [
    "price_sensitivity",
    "trust_loss",
    "fairness_perception",
    "substitution_option",
    "identity_alignment",
    "service_access_constraint",
    "loss_aversion",
    "social_diffusion_sensitivity",
]
PARAMETER_FAMILIES = [
    "mechanism_activation",
    "segment_sensitivity",
    "propagation_edge",
    "uncertainty_calibration",
    "guard_penalty",
]


def build_r8_learnable_mechanism_bundle(
    *,
    artifact_id: str,
    run_id: str,
    case_id: str = "generic-public-service-policy-change",
    rollout_count: int = 50,
    observed_reject_proxy: float | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    case = get_r6_case_template(non_empty_string(case_id, field="case_id"))

    graph = _mechanism_graph(f"{artifact_id}-mechanism-causal-graph", run_id, case)
    registry = _parameter_registry(
        f"{artifact_id}-operator-parameter-registry",
        run_id,
        graph,
    )
    rollout = _rollout_distribution(
        f"{artifact_id}-rollout-distribution",
        run_id,
        case,
        graph,
        registry,
        rollout_count,
    )
    interval = _interval_report(
        f"{artifact_id}-risk-interval-calibration",
        run_id,
        rollout,
    )
    ranking = _risk_ranking_report(f"{artifact_id}-risk-ranking", run_id, case, rollout)
    attribution = _outcome_attribution_report(
        f"{artifact_id}-outcome-attribution",
        run_id,
        case,
        rollout,
        ranking,
        observed_reject_proxy,
    )
    update = _operator_update_candidate(
        f"{artifact_id}-operator-update-candidate",
        run_id,
        attribution,
    )
    support = _product_support_gate(
        f"{artifact_id}-product-support-gate",
        run_id,
        interval,
        ranking,
        attribution,
        update,
    )
    artifacts = {
        "r8_mechanism_causal_graph_manifest": graph,
        "r8_operator_parameter_registry": registry,
        "r8_rollout_distribution": rollout,
        "r8_risk_interval_calibration_report": interval,
        "r8_risk_ranking_report": ranking,
        "r8_outcome_attribution_report": attribution,
        "r8_operator_update_candidate": update,
        "r8_product_support_gate": support,
    }
    payload = {
        "schema_version": R8_BUNDLE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "case_id": case["case_id"],
        "status": "r8_contract_ready_guarded",
        "claim_boundary": R8_CLAIM_BOUNDARY,
        "source_refs": [
            case["case_id"],
            case["scenario"]["scenario_id"],
            *case["scenario"]["source_refs"],
        ],
        "artifacts": artifacts,
        "acceptance_gates": {
            "artifact_contracts_present": True,
            "source_refs_present": True,
            "product_guard_consumable": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            "R8 exposes a guarded learnable-mechanism artifact contract.",
            (
                "R8 can be compared against R7 v2 and conservative baselines "
                "before product escalation."
            ),
        ],
        "blocked_claims": [
            "精准预测系统",
            "R8 validated",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy superiority",
        ],
    }
    assert_strict_json(payload)
    return payload


def _artifact(
    *,
    schema_version: str,
    artifact_id: str,
    run_id: str,
    source_refs: list[str],
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "schema_version": schema_version,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "source_refs": source_refs,
        "claim_boundary": R8_CLAIM_BOUNDARY,
    }
    payload.update(extra)
    return payload


def _mechanism_graph(
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
) -> dict[str, Any]:
    nodes = [
        {
            "node_id": "scenario_shock",
            "node_type": "input",
            "source_refs": [case["scenario"]["scenario_id"]],
        },
        *[
            {
                "node_id": mechanism,
                "node_type": "mechanism",
                "source_refs": case["scenario"]["source_refs"],
            }
            for mechanism in MECHANISM_CATALOG
        ],
        {
            "node_id": "segment_response",
            "node_type": "latent_state",
            "source_refs": [case["case_id"]],
        },
        {
            "node_id": "interaction_propagation",
            "node_type": "operator",
            "source_refs": [case["case_id"]],
        },
        {
            "node_id": "risk_distribution",
            "node_type": "output",
            "source_refs": [case["case_id"]],
        },
    ]
    edges = [
        {
            "edge_id": f"scenario_to_{mechanism}",
            "source_node": "scenario_shock",
            "target_node": mechanism,
            "effect_direction": "increase",
            "effect_strength": (
                0.45 if mechanism in case["scenario"]["impact_dimensions"] else 0.2
            ),
            "uncertainty": 0.12,
            "evidence_source": "rule:scenario_impact_dimension",
            "learnable": True,
            "guard_constraints": ["bounded_update", "holdout_required"],
        }
        for mechanism in MECHANISM_CATALOG
    ]
    edges.extend(
        [
            {
                "edge_id": "mechanisms_to_segment_response",
                "source_node": "mechanism_activation",
                "target_node": "segment_response",
                "effect_direction": "mixed",
                "effect_strength": 0.5,
                "uncertainty": 0.1,
                "evidence_source": "rule:segment_static_traits",
                "learnable": True,
                "guard_constraints": ["non_regression_required"],
            },
            {
                "edge_id": "segment_response_to_interaction",
                "source_node": "segment_response",
                "target_node": "interaction_propagation",
                "effect_direction": "amplify_or_buffer",
                "effect_strength": 0.35,
                "uncertainty": 0.16,
                "evidence_source": "rule:interaction_graph_fixture",
                "learnable": True,
                "guard_constraints": ["false_alarm_guard"],
            },
        ]
    )
    return _artifact(
        schema_version="r8-mechanism-causal-graph-manifest-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[
            case["case_id"],
            case["scenario"]["scenario_id"],
            *case["scenario"]["source_refs"],
        ],
        graph_nodes=nodes,
        graph_edges=edges,
        mechanism_catalog=MECHANISM_CATALOG,
        evidence_sources=[
            "rule:scenario_impact_dimension",
            "rule:segment_static_traits",
            "rule:interaction_graph_fixture",
        ],
        learnable_parameters=[edge["edge_id"] for edge in edges if edge["learnable"]],
        non_learnable_constraints=[
            "field_outcome_validated",
            "runtime_default_allowed",
            "blocked_claims",
        ],
        llm_boundary={
            "llm_may_generate_candidate_mechanisms": True,
            "llm_may_generate_customer_narrative_draft": True,
            "llm_can_set_field_outcome_validated": False,
            "llm_can_set_runtime_default_allowed": False,
            "structured_output_required": True,
        },
    )


def _parameter_registry(
    artifact_id: str,
    run_id: str,
    graph: dict[str, Any],
) -> dict[str, Any]:
    parameters = []
    for index, family in enumerate(PARAMETER_FAMILIES):
        parameters.append(
            {
                "parameter_id": f"{family}:{index}",
                "parameter_family": family,
                "current_value": round(0.2 + index * 0.1, 3),
                "allowed_range": [0.0, 1.0],
                "evidence_level": "fixture_rule",
                "last_update_source": graph["artifact_id"],
                "runtime_default_allowed": False,
                "rollback_policy": "revert_to_previous_registry_value",
            }
        )
    return _artifact(
        schema_version="r8-operator-parameter-registry-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[graph["artifact_id"]],
        parameter_families=PARAMETER_FAMILIES,
        parameters=parameters,
        runtime_default_allowed=False,
    )


def _rollout_distribution(
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
    graph: dict[str, Any],
    registry: dict[str, Any],
    rollout_count: int,
) -> dict[str, Any]:
    static_prior = sum(
        segment["weight"] * segment["static_response_prior"]["reject"]
        for segment in case["prior_segments"]
    )
    interaction_shift = (
        0.06 if case["case_id"] == "generic-public-service-policy-change" else -0.03
    )
    candidate_shift = interaction_shift * 0.85
    return _artifact(
        schema_version="r8-rollout-distribution-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[graph["artifact_id"], registry["artifact_id"]],
        rollout_count=rollout_count,
        seed_policy="deterministic:0..rollout_count-1",
        no_interaction_distribution={
            "median": round(static_prior, 4),
            "p10": round(max(0.0, static_prior - 0.06), 4),
            "p90": round(min(1.0, static_prior + 0.06), 4),
        },
        interaction_distribution={
            "median": round(static_prior + interaction_shift, 4),
            "p10": round(max(0.0, static_prior + interaction_shift - 0.09), 4),
            "p90": round(min(1.0, static_prior + interaction_shift + 0.09), 4),
        },
        candidate_update_distribution={
            "median": round(static_prior + candidate_shift, 4),
            "p10": round(max(0.0, static_prior + candidate_shift - 0.08), 4),
            "p90": round(min(1.0, static_prior + candidate_shift + 0.08), 4),
        },
        uncertainty_breakdown={
            "prior": 0.06,
            "mechanism": 0.05,
            "propagation": 0.06,
            "outcome_proxy": 0.08,
        },
        interval_width=0.18,
        over_width_penalty=0.0,
    )


def _interval_report(
    artifact_id: str,
    run_id: str,
    rollout: dict[str, Any],
) -> dict[str, Any]:
    return _artifact(
        schema_version="r8-risk-interval-calibration-report-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout["artifact_id"]],
        trend_direction_accuracy=None,
        interval_coverage=None,
        mean_interval_width=rollout["interval_width"],
        interval_efficiency=None,
        coverage_by_case_family={},
        indeterminate_rate=0.0,
        over_width_blocked=False,
        claim_status="contract_only",
    )


def _risk_ranking_report(
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
    rollout: dict[str, Any],
) -> dict[str, Any]:
    ranked = sorted(
        [
            {
                "segment_id": segment["segment_id"],
                "risk_score": round(
                    segment["static_response_prior"]["reject"] + 0.04,
                    4,
                ),
                "risk_type": "interaction_amplified_risk",
                "source_refs": segment["source_refs"],
            }
            for segment in case["prior_segments"]
        ],
        key=lambda item: item["risk_score"],
        reverse=True,
    )
    return _artifact(
        schema_version="r8-risk-ranking-report-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout["artifact_id"], case["case_id"]],
        top_k_hit_rate=None,
        risk_ranking_quality=None,
        static_prior_miss_recovery_rate=None,
        false_alarm_rate=None,
        segment_precision=None,
        segment_recall=None,
        static_hidden_risk_segments=[
            item for item in ranked if item["risk_score"] >= 0.4
        ],
        interaction_amplified_segments=ranked,
    )


def _outcome_attribution_report(
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
    rollout: dict[str, Any],
    ranking: dict[str, Any],
    observed_reject_proxy: float | None,
) -> dict[str, Any]:
    predicted = rollout["interaction_distribution"]["median"]
    if observed_reject_proxy is not None:
        observed = float(observed_reject_proxy)
        residual = round(observed - predicted, 4)
        direction = "increase" if residual > 0 else "decrease"
        segment_count = max(1, len(ranking["interaction_amplified_segments"]))
        return _artifact(
            schema_version="r8-outcome-attribution-report-v1",
            artifact_id=artifact_id,
            run_id=run_id,
            source_refs=[rollout["artifact_id"], ranking["artifact_id"], case["case_id"]],
            outcome_reject_proxy=round(observed, 4),
            prediction_median=predicted,
            outcome_residual=residual,
            attribution_by_mechanism=[
                {
                    "mechanism": "service_access_constraint",
                    "error_type": "mechanism_strength_error",
                    "recommended_update_direction": direction,
                    "residual_share": 0.45,
                    "source_refs": [rollout["artifact_id"]],
                },
                {
                    "mechanism": "fairness_perception",
                    "error_type": "mechanism_direction_supported",
                    "recommended_update_direction": direction,
                    "residual_share": 0.3,
                    "source_refs": [rollout["artifact_id"]],
                },
            ],
            attribution_by_edge=[
                {
                    "edge_id": "segment_response_to_interaction",
                    "error_type": "propagation_strength_error",
                    "recommended_update_direction": direction,
                    "residual_share": 0.25,
                    "source_refs": [rollout["artifact_id"]],
                }
            ],
            attribution_by_segment=[
                {
                    "segment_id": item["segment_id"],
                    "error_type": "segment_sensitivity_error",
                    "recommended_update_direction": direction,
                    "residual_share": round(0.2 / segment_count, 4),
                    "source_refs": item["source_refs"],
                }
                for item in ranking["interaction_amplified_segments"]
            ],
            interval_error_type=(
                "covered"
                if rollout["interaction_distribution"]["p10"]
                <= observed
                <= rollout["interaction_distribution"]["p90"]
                else "missed_interval"
            ),
            false_alarm_sources=[],
            missed_risk_sources=[],
            unexplained_error=0.0,
        )
    return _artifact(
        schema_version="r8-outcome-attribution-report-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[rollout["artifact_id"], ranking["artifact_id"], case["case_id"]],
        outcome_residual=None,
        attribution_by_mechanism=[],
        attribution_by_edge=[],
        attribution_by_segment=[],
        interval_error_type="not_evaluated_without_outcome",
        false_alarm_sources=[],
        missed_risk_sources=[],
        unexplained_error="not_evaluated_without_outcome",
    )


def _operator_update_candidate(
    artifact_id: str,
    run_id: str,
    attribution: dict[str, Any],
) -> dict[str, Any]:
    updated_parameters: list[dict[str, Any]]
    if attribution["outcome_residual"] is None:
        updated_parameters = []
        expected_metric_delta: dict[str, Any] = {}
        rejected_reason = "blocked_until_outcome_and_holdout"
        guard_checks = {"holdout_required": True, "runtime_default_allowed": False}
    else:
        residual = float(attribution["outcome_residual"])
        bounded_delta = round(max(-0.08, min(0.08, residual * 0.5)), 4)
        updated_parameters = [
            {
                "parameter_id": "mechanism_activation:service_access_constraint",
                "parameter_family": "mechanism_activation",
                "current_value": 0.4,
                "delta": bounded_delta,
                "candidate_value": round(max(0.0, min(1.0, 0.4 + bounded_delta)), 4),
                "max_abs_delta": 0.08,
                "source_attribution_id": attribution["artifact_id"],
            },
            {
                "parameter_id": "propagation_edge:segment_response_to_interaction",
                "parameter_family": "propagation_edge",
                "current_value": 0.35,
                "delta": round(bounded_delta * 0.5, 4),
                "candidate_value": round(
                    max(0.0, min(1.0, 0.35 + bounded_delta * 0.5)),
                    4,
                ),
                "max_abs_delta": 0.08,
                "source_attribution_id": attribution["artifact_id"],
            },
        ]
        expected_metric_delta = {"mean_absolute_error": "decrease"}
        rejected_reason = "pending_holdout_review"
        guard_checks = {
            "bounded_update": True,
            "holdout_required": True,
            "robustness_required": True,
            "runtime_default_allowed": False,
        }
    return _artifact(
        schema_version="r8-operator-update-candidate-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[attribution["artifact_id"]],
        candidate_id=f"{artifact_id}:candidate-001",
        updated_parameters=updated_parameters,
        expected_metric_delta=expected_metric_delta,
        guard_checks=guard_checks,
        holdout_results=[],
        robustness_results=[],
        accepted=False,
        rejected_reason=rejected_reason,
        runtime_default_allowed=False,
    )


def _product_support_gate(
    artifact_id: str,
    run_id: str,
    interval: dict[str, Any],
    ranking: dict[str, Any],
    attribution: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]:
    return _artifact(
        schema_version="r8-product-support-gate-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[
            interval["artifact_id"],
            ranking["artifact_id"],
            attribution["artifact_id"],
            update["artifact_id"],
        ],
        trend_supported="contract_only",
        interval_supported="contract_only",
        risk_ranking_supported="contract_only",
        abnormal_segment_supported="contract_only",
        mechanism_explanation_supported="guarded",
        outcome_learning_supported="blocked_until_outcome",
        field_outcome_validated=False,
        runtime_default_allowed=False,
        blocked_claims=[
            "R8 validated",
            "runtime default ready",
            "field validated",
            "accuracy superiority",
        ],
        allowed_claims=[
            "R8 contract artifacts can be inspected and compared under guard."
        ],
    )


def write_r8_learnable_mechanism_bundle(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r8_learnable_mechanism_bundle(**kwargs))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r8-learnable-mechanism-bundle-current-001")
    parser.add_argument("--run-id", default="r8-learnable-mechanism-current")
    parser.add_argument("--case-id", default="generic-public-service-policy-change")
    parser.add_argument("--rollout-count", type=int, default=50)
    parser.add_argument("--observed-reject-proxy", type=float, default=None)
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r8_learnable_mechanism_bundle/"
            "r8-learnable-mechanism-bundle-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r8_learnable_mechanism_bundle(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        case_id=args.case_id,
        rollout_count=args.rollout_count,
        observed_reject_proxy=args.observed_reject_proxy,
    )
    artifact = build_r8_learnable_mechanism_bundle(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        case_id=args.case_id,
        rollout_count=args.rollout_count,
        observed_reject_proxy=args.observed_reject_proxy,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output),
                "status": artifact["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
