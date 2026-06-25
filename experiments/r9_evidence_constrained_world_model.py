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
        "status": "r9_artifact_contract_ready_guarded",
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
        status="r9_route_outputs_contract_ready",
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
        "claim_boundary": R9_CLAIM_BOUNDARY,
        "source_refs": source_refs,
        "route_contract": {
            "source_backed_only": True,
            "llm_direct_prediction_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "metrics": _uncomputed_metrics(),
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
