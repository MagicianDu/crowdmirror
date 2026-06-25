from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact


R9_CLAIM_BOUNDARY = (
    "R9 evidence-constrained interaction world model artifact. It defines "
    "source-backed mechanism, retrieval, and constrained-agent rollout routes "
    "plus a combination matrix for guarded evaluation only; it is not field "
    "validation, not point-prediction evidence, and not runtime default "
    "authorization."
)
R9_WORLD_MODEL_BUNDLE_SCHEMA_VERSION = "r9-world-model-bundle-v1"
R9_ROUTE_IDS = [
    "route_a_evidence_constrained_mechanism_operator",
    "route_b_semantic_precedent_retrieval",
    "route_c_constrained_multi_agent_rollout",
]
R9_COMBINATION_IDS = [
    "A_only",
    "B_only",
    "C_only",
    "A+B",
    "A+C",
    "B+C",
    "A+B+C",
]
R9_METRIC_IDS = [
    "trend_direction_accuracy",
    "interval_coverage",
    "risk_ranking_quality",
    "false_alarm_rate",
    "static_prior_miss_recovery_rate",
    "decision_value_score",
]
R9_BASELINE_IDS = [
    "static_prior",
    "r6_learning_counterfactual",
    "r7_v2_guarded_baseline",
    "r8_diagnostic_method",
]
R9_DEFAULT_SOURCE_REFS = [
    "docs/superpowers/specs/2026-06-26-r9-evidence-constrained-interaction-world-model-spec.md",
    "experiments/results/r8_stop_loss_diagnosis/r8-stop-loss-diagnosis-current-001.json",
    (
        "experiments/results/r8_product_failure_diagnosis_package/"
        "r8-product-failure-diagnosis-package-current-001.json"
    ),
]


def build_r9_world_model_bundle(
    *,
    artifact_id: str,
    run_id: str,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    refs = _source_refs(source_refs)
    manifest = _world_model_manifest(
        artifact_id=f"{artifact_id}-world-model-manifest",
        run_id=run_id,
        source_refs=refs,
    )
    route_outputs = _route_outputs(
        artifact_id=f"{artifact_id}-route-outputs",
        run_id=run_id,
        source_refs=refs,
    )
    combination_matrix = _combination_matrix(
        artifact_id=f"{artifact_id}-combination-matrix",
        run_id=run_id,
        source_refs=refs,
    )
    support_gate = _product_support_gate(
        artifact_id=f"{artifact_id}-product-support-gate",
        run_id=run_id,
        source_refs=refs,
        route_outputs=route_outputs,
        combination_matrix=combination_matrix,
    )
    payload = {
        "schema_version": R9_WORLD_MODEL_BUNDLE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r9_route_mvp_ready_guarded",
        "product_positioning": "人群反应趋势与风险区间模拟器",
        "claim_boundary": R9_CLAIM_BOUNDARY,
        "source_refs": refs,
        "artifacts": {
            "r9_world_model_manifest": manifest,
            "r9_route_outputs": route_outputs,
            "r9_combination_matrix": combination_matrix,
            "r9_product_support_gate": support_gate,
        },
        "acceptance_gates": {
            "artifact_contracts_present": True,
            "route_artifacts_present": True,
            "route_mvp_outputs_present": True,
            "combination_matrix_present": True,
            "source_refs_present": True,
            "product_guard_consumable": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "allowed_claims": [
            "R9 L0 artifact contract is ready for guarded method exploration.",
            "R9 routes and combinations can be evaluated against existing baselines.",
        ],
        "blocked_claims": [
            "R9 validated",
            "R9 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    assert_strict_json(payload)
    return payload


def write_r9_world_model_bundle(*, output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r9_world_model_bundle(**kwargs))


def _world_model_manifest(
    *,
    artifact_id: str,
    run_id: str,
    source_refs: list[str],
) -> dict[str, Any]:
    return _artifact(
        schema_version="r9-world-model-manifest-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=source_refs,
        status="r9_world_model_manifest_ready",
        method_name="证据约束交互世界模型",
        method_contract={
            "static_prior_is_foundation": True,
            "external_evidence_required_for_escalation": True,
            "interaction_rollout_is_hypothesis_generator": True,
            "product_guard_required": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        route_ids=R9_ROUTE_IDS,
        combination_ids=R9_COMBINATION_IDS,
        baseline_ids=R9_BASELINE_IDS,
    )


def _route_outputs(
    *,
    artifact_id: str,
    run_id: str,
    source_refs: list[str],
) -> dict[str, Any]:
    routes = {
        route_id: _route_output(route_id=route_id, source_refs=source_refs)
        for route_id in R9_ROUTE_IDS
    }
    return _artifact(
        schema_version="r9-route-outputs-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=source_refs,
        status="r9_route_outputs_mvp_ready_guarded",
        routes=routes,
        metrics_schema=_metric_schema(),
    )


def _route_output(*, route_id: str, source_refs: list[str]) -> dict[str, Any]:
    route_names = {
        "route_a_evidence_constrained_mechanism_operator": "证据约束机制算子",
        "route_b_semantic_precedent_retrieval": "语义案例检索与先例约束",
        "route_c_constrained_multi_agent_rollout": "受约束多主体交互 rollout",
    }
    route_goals = {
        "route_a_evidence_constrained_mechanism_operator": (
            "learn mechanism activation, propagation edges, and bounded updates"
        ),
        "route_b_semantic_precedent_retrieval": (
            "retrieve source-backed precedent cases to constrain mechanisms"
        ),
        "route_c_constrained_multi_agent_rollout": (
            "generate structured interaction traces and anomaly candidates"
        ),
    }
    return {
        "route_id": route_id,
        "route_name": route_names[route_id],
        "route_goal": route_goals[route_id],
        "route_status": "r9_route_mvp_output_ready_guarded",
        "claim_boundary": R9_CLAIM_BOUNDARY,
        "source_refs": source_refs,
        "route_contract": {
            "source_backed_only": True,
            "llm_direct_prediction_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "output_contract": {
            "trend_output_present": True,
            "risk_interval_present": True,
            "risk_distribution_present": True,
            "abnormal_segments_present": True,
            "mechanism_trace_present": True,
            "failure_reasons_present": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "trend_output": _route_trend_output(route_id),
        "risk_interval": _route_risk_interval(route_id),
        "risk_distribution": _route_risk_distribution(route_id),
        "abnormal_segments": _route_abnormal_segments(route_id),
        "mechanism_trace": _route_mechanism_trace(route_id),
        "failure_reasons": _route_failure_reasons(route_id),
        "metrics": _uncomputed_metrics(),
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "required_next_evidence": [
            "route-specific runnable implementation",
            "baseline comparison",
            "holdout or perturbation guard",
        ],
        "blocked_claims": [
            "route validated",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
        ],
    }


def _route_trend_output(route_id: str) -> dict[str, Any]:
    trend_by_route = {
        "route_a_evidence_constrained_mechanism_operator": {
            "direction": "risk_increase",
            "confidence": 0.62,
            "rationale": (
                "mechanism operator flags trust_loss and service_access_constraint "
                "as bounded risk amplifiers"
            ),
        },
        "route_b_semantic_precedent_retrieval": {
            "direction": "risk_increase",
            "confidence": 0.58,
            "rationale": (
                "precedent fixture links price/service changes to moderate "
                "customer rejection risk"
            ),
        },
        "route_c_constrained_multi_agent_rollout": {
            "direction": "risk_increase",
            "confidence": 0.55,
            "rationale": (
                "constrained rollout produces interaction concern signals in "
                "price-sensitive and trust-sensitive segments"
            ),
        },
    }
    return trend_by_route[route_id]


def _route_risk_interval(route_id: str) -> dict[str, Any]:
    interval_by_route = {
        "route_a_evidence_constrained_mechanism_operator": (0.30, 0.37, 0.45),
        "route_b_semantic_precedent_retrieval": (0.28, 0.35, 0.44),
        "route_c_constrained_multi_agent_rollout": (0.31, 0.39, 0.50),
    }
    lower, median, upper = interval_by_route[route_id]
    return {
        "lower": lower,
        "median": median,
        "upper": upper,
        "unit": "reject_probability",
        "calibration_status": "mvp_fixture_not_holdout_validated",
    }


def _route_risk_distribution(route_id: str) -> list[dict[str, Any]]:
    risk_scores = {
        "route_a_evidence_constrained_mechanism_operator": [0.46, 0.38, 0.27],
        "route_b_semantic_precedent_retrieval": [0.43, 0.36, 0.29],
        "route_c_constrained_multi_agent_rollout": [0.49, 0.41, 0.31],
    }
    segment_ids = [
        "price_sensitive_users",
        "trust_sensitive_users",
        "low_exposure_users",
    ]
    mechanism_ids = [
        "price_sensitivity",
        "trust_loss",
        "service_access_constraint",
    ]
    return [
        {
            "segment_id": segment_id,
            "risk_score": risk_score,
            "top_mechanism": mechanism_id,
            "claim_status": "diagnostic_mvp",
        }
        for segment_id, risk_score, mechanism_id in zip(
            segment_ids,
            risk_scores[route_id],
            mechanism_ids,
            strict=True,
        )
    ]


def _route_abnormal_segments(route_id: str) -> list[dict[str, Any]]:
    top_reason = {
        "route_a_evidence_constrained_mechanism_operator": (
            "bounded mechanism operator assigns highest sensitivity to price change"
        ),
        "route_b_semantic_precedent_retrieval": (
            "retrieved precedent cases concentrate risk in price-sensitive groups"
        ),
        "route_c_constrained_multi_agent_rollout": (
            "agent interaction trace amplifies complaint sharing in high-sensitivity group"
        ),
    }
    return [
        {
            "segment_id": "price_sensitive_users",
            "risk_flag": "top_abnormal_segment",
            "reason": top_reason[route_id],
            "source_status": "fixture_level_evidence",
        }
    ]


def _route_mechanism_trace(route_id: str) -> list[dict[str, Any]]:
    trace_by_route = {
        "route_a_evidence_constrained_mechanism_operator": [
            ("scenario_shock", "price_sensitivity", "activates"),
            ("price_sensitivity", "reject_probability", "amplifies"),
        ],
        "route_b_semantic_precedent_retrieval": [
            ("semantic_query", "precedent_case_cluster", "retrieves"),
            ("precedent_case_cluster", "risk_interval", "calibrates"),
        ],
        "route_c_constrained_multi_agent_rollout": [
            ("segment_agents", "concern_signal", "exchange"),
            ("concern_signal", "abnormal_segment_risk", "amplifies"),
        ],
    }
    return [
        {
            "source_node": source,
            "target_node": target,
            "effect": effect,
            "evidence_status": "mvp_fixture_not_field_validated",
        }
        for source, target, effect in trace_by_route[route_id]
    ]


def _route_failure_reasons(route_id: str) -> list[dict[str, str]]:
    reason_by_route = {
        "route_a_evidence_constrained_mechanism_operator": (
            "mechanism parameters are fixture-level and not holdout validated"
        ),
        "route_b_semantic_precedent_retrieval": (
            "precedent retrieval uses a minimal fixture rather than a real case index"
        ),
        "route_c_constrained_multi_agent_rollout": (
            "agent rollout is deterministic fixture output and not provider-stability tested"
        ),
    }
    return [
        {
            "reason_id": "field_outcome_missing",
            "description": "no customer or field outcome is attached to this route output",
        },
        {
            "reason_id": "route_mvp_not_validated",
            "description": reason_by_route[route_id],
        },
    ]


def _combination_matrix(
    *,
    artifact_id: str,
    run_id: str,
    source_refs: list[str],
) -> dict[str, Any]:
    metrics_schema = _metric_schema()
    return _artifact(
        schema_version="r9-combination-matrix-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=source_refs,
        status="r9_combination_matrix_contract_ready",
        baseline_ids=R9_BASELINE_IDS,
        metrics_schema=metrics_schema,
        combinations=[
            {
                "combination_id": combination_id,
                "route_ids": _combination_routes(combination_id),
                "source_refs": source_refs,
                "metrics_schema": metrics_schema,
                "metrics": _uncomputed_metrics(),
                "claim_status": "not_evaluated_l0_contract_only",
                "field_outcome_validated": False,
                "runtime_default_allowed": False,
            }
            for combination_id in R9_COMBINATION_IDS
        ],
        stop_loss_policy={
            "trigger": "no combination beats r7_v2_guarded_baseline under guard metrics",
            "downgrade_to": "diagnostic_method_experiment",
        },
    )


def _product_support_gate(
    *,
    artifact_id: str,
    run_id: str,
    source_refs: list[str],
    route_outputs: dict[str, Any],
    combination_matrix: dict[str, Any],
) -> dict[str, Any]:
    return _artifact(
        schema_version="r9-product-support-gate-v1",
        artifact_id=artifact_id,
        run_id=run_id,
        source_refs=[
            *source_refs,
            route_outputs["artifact_id"],
            combination_matrix["artifact_id"],
        ],
        status="r9_product_support_gate_ready_guarded",
        product_support_status="contract_ready_not_method_validated",
        route_count=len(route_outputs["routes"]),
        combination_count=len(combination_matrix["combinations"]),
        field_outcome_validated=False,
        runtime_default_allowed=False,
        source_backed_only=True,
        allowed_claims=[
            "R9 artifact contract defines evidence-constrained routes and combination matrix.",
            "R9 can be evaluated against R6/R7/R8 baselines before Product escalation.",
        ],
        blocked_claims=[
            "R9 validated",
            "R9 supports Product core method by default",
            "runtime default ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy superiority",
        ],
    )


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
        "claim_boundary": R9_CLAIM_BOUNDARY,
    }
    payload.update(extra)
    return payload


def _metric_schema() -> list[str]:
    return list(R9_METRIC_IDS)


def _uncomputed_metrics() -> dict[str, dict[str, Any]]:
    return {
        metric_id: {
            "value": None,
            "status": "not_computed_l0_contract_only",
        }
        for metric_id in R9_METRIC_IDS
    }


def _combination_routes(combination_id: str) -> list[str]:
    route_map = {
        "A": "route_a_evidence_constrained_mechanism_operator",
        "B": "route_b_semantic_precedent_retrieval",
        "C": "route_c_constrained_multi_agent_rollout",
    }
    return [
        route_map[token]
        for token in combination_id.replace("_only", "").split("+")
    ]


def _source_refs(source_refs: list[str] | None) -> list[str]:
    refs = source_refs or R9_DEFAULT_SOURCE_REFS
    return [
        non_empty_string(ref, field=f"source_refs[{index}]")
        for index, ref in enumerate(refs)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r9-world-model-bundle-current-001")
    parser.add_argument("--run-id", default="r9-world-model-bundle-current")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r9_world_model_bundle/"
            "r9-world-model-bundle-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r9_world_model_bundle(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = build_r9_world_model_bundle(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
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
