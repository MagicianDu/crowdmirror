from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROUTE_B_ROBUST_SCORE_SCHEMA_VERSION = "policy-reaction-route-b-robust-score-v1"
S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
S2PC_RUNTIME_EFFECT_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-effect-v1"
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"
DEFAULT_ALPHA = 1.0
DEFAULT_BETA = 1.0
DEFAULT_GAMMA = 0.001


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_route_b_robust_score(
    *,
    candidate: dict[str, Any],
    effect_artifacts: list[dict[str, Any]],
    artifact_id: str,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
    loss_metric: str = DEFAULT_LOSS_METRIC,
    min_improved_runs: int = 2,
    max_regressed_runs: int = 0,
) -> dict[str, Any]:
    _validate_candidate(candidate)
    if not effect_artifacts:
        raise ValueError("effect_artifacts must not be empty")
    validated_effects = [
        _validate_effect_artifact(
            artifact,
            candidate_id=candidate["candidate_id"],
            loss_metric=loss_metric,
        )
        for artifact in effect_artifacts
    ]
    runtime_losses = [float(artifact["s2pc_runtime_loss"]) for artifact in validated_effects]
    baseline_losses = [float(artifact["baseline_loss"]) for artifact in validated_effects]
    improved_count = sum(
        1 for artifact in validated_effects if artifact["overall_status"] == "improved"
    )
    regressed_count = sum(
        1 for artifact in validated_effects if artifact["overall_status"] == "regressed"
    )
    no_change_count = sum(
        1 for artifact in validated_effects if artifact["overall_status"] == "no_change"
    )
    mean_loss = _mean(runtime_losses)
    loss_std = _std(runtime_losses)
    worst_case_loss = max(runtime_losses)
    baseline_mean_loss = _mean(baseline_losses)
    complexity_penalty = _complexity_penalty(candidate)
    robust_score = (
        mean_loss
        + alpha * loss_std
        + beta * worst_case_loss
        + gamma * complexity_penalty
    )
    overall_status = _overall_status(
        improved_count=improved_count,
        regressed_count=regressed_count,
        min_improved_runs=min_improved_runs,
        max_regressed_runs=max_regressed_runs,
    )
    artifact = {
        "schema_version": ROUTE_B_ROBUST_SCORE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "loss_metric": loss_metric,
        "candidate_id": candidate["candidate_id"],
        "candidate_generator": candidate.get("generator"),
        "robust_objective": {
            "mean_loss": _round_float(mean_loss),
            "instability_penalty": _round_float(loss_std),
            "worst_case_loss": _round_float(worst_case_loss),
            "complexity_penalty": _round_float(complexity_penalty),
            "alpha": _round_float(alpha),
            "beta": _round_float(beta),
            "gamma": _round_float(gamma),
            "robust_score": _round_float(robust_score),
        },
        "repeat_summary": {
            "effect_count": len(validated_effects),
            "improved_count": improved_count,
            "regressed_count": regressed_count,
            "no_change_count": no_change_count,
            "baseline_mean_loss": _round_float(baseline_mean_loss),
            "relative_mean_improvement": _round_float(
                (baseline_mean_loss - mean_loss) / baseline_mean_loss
            )
            if baseline_mean_loss > 0.0
            else None,
        },
        "scale_axes": _scale_axes(validated_effects),
        "effect_artifact_ids": [artifact["artifact_id"] for artifact in validated_effects],
        "source_split_contract": {
            **candidate["source_split_contract"],
            "robust_objective_evaluation": "heldout_repeat_axes",
        },
        "stop_loss_policy": {
            "min_improved_runs": min_improved_runs,
            "max_regressed_runs": max_regressed_runs,
            "rule": (
                "require_at_least_min_improved_runs_and_no_more_than_max_regressed_runs"
            ),
        },
        "claim_boundary": (
            "Route B robust score is repeat-aware local held-out optimization evidence, not field validation."
        ),
        "claim_boundaries": [
            "Route B evaluates candidates under repeat-aware held-out loss, not single-run prompt quality alone.",
            "A candidate must be judged by mean, instability, and worst-case behavior together.",
            "This artifact does not establish cross-source or production-field generalization.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_route_b_robust_score(
    path: str | Path,
    *,
    candidate_path: str | Path,
    effect_artifact_paths: list[str | Path],
    artifact_id: str,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
    loss_metric: str = DEFAULT_LOSS_METRIC,
    min_improved_runs: int = 2,
    max_regressed_runs: int = 0,
) -> Path:
    artifact = build_policy_reaction_route_b_robust_score(
        candidate=load_json_artifact(candidate_path),
        effect_artifacts=[load_json_artifact(path) for path in effect_artifact_paths],
        artifact_id=artifact_id,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        loss_metric=loss_metric,
        min_improved_runs=min_improved_runs,
        max_regressed_runs=max_regressed_runs,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--effect-artifact", action="append", dest="effect_artifacts", required=True)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-route-b-robust-score-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-route-b-robust-score-current-001.json"
        ),
    )
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    parser.add_argument("--beta", type=float, default=DEFAULT_BETA)
    parser.add_argument("--gamma", type=float, default=DEFAULT_GAMMA)
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    parser.add_argument("--min-improved-runs", type=int, default=2)
    parser.add_argument("--max-regressed-runs", type=int, default=0)
    args = parser.parse_args()
    output_path = write_policy_reaction_route_b_robust_score(
        args.output,
        candidate_path=args.candidate,
        effect_artifact_paths=args.effect_artifacts,
        artifact_id=args.artifact_id,
        alpha=args.alpha,
        beta=args.beta,
        gamma=args.gamma,
        loss_metric=args.loss_metric,
        min_improved_runs=args.min_improved_runs,
        max_regressed_runs=args.max_regressed_runs,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["overall_status"],
                "robust_score": artifact["robust_objective"]["robust_score"],
                "improved_count": artifact["repeat_summary"]["improved_count"],
                "regressed_count": artifact["repeat_summary"]["regressed_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("candidate has unsupported schema_version")
    for field_name in ("candidate_id", "source_split_contract", "best_candidate"):
        if field_name not in candidate:
            raise ValueError(f"candidate missing {field_name}")


def _validate_effect_artifact(
    artifact: dict[str, Any],
    *,
    candidate_id: str,
    loss_metric: str,
) -> dict[str, Any]:
    if artifact.get("schema_version") != S2PC_RUNTIME_EFFECT_SCHEMA_VERSION:
        raise ValueError("effect artifact has unsupported schema_version")
    if artifact.get("loss_metric") != loss_metric:
        raise ValueError("effect artifact uses unexpected loss_metric")
    if artifact.get("s2pc_candidate_id") != candidate_id:
        raise ValueError("effect artifact candidate_id mismatch")
    for field_name in (
        "artifact_id",
        "overall_status",
        "baseline_loss",
        "s2pc_runtime_loss",
        "product_runtime_scale",
    ):
        if field_name not in artifact:
            raise ValueError(f"effect artifact missing {field_name}")
    return artifact


def _complexity_penalty(candidate: dict[str, Any]) -> float:
    best_candidate = candidate.get("best_candidate", {})
    patches = best_candidate.get("parameter_patches", [])
    components = candidate.get("candidate_prompt_components", {})
    segment_prompts = components.get("segment_prompt", {})
    anchors = components.get("calibration_anchor", {})
    return float(len(patches) + len(segment_prompts) + len(anchors))


def _scale_axes(effect_artifacts: list[dict[str, Any]]) -> dict[str, list[int]]:
    persona_counts = sorted(
        {
            int(artifact["product_runtime_scale"]["persona_count"])
            for artifact in effect_artifacts
            if "persona_count" in artifact["product_runtime_scale"]
        }
    )
    scenario_counts = sorted(
        {
            int(artifact["product_runtime_scale"]["scenario_count"])
            for artifact in effect_artifacts
            if "scenario_count" in artifact["product_runtime_scale"]
        }
    )
    seeds = sorted(
        {
            int(artifact["product_runtime_scale"]["seed"])
            for artifact in effect_artifacts
            if "seed" in artifact["product_runtime_scale"]
        }
    )
    return {
        "persona_counts": persona_counts,
        "scenario_counts": scenario_counts,
        "seeds": seeds,
    }


def _overall_status(
    *,
    improved_count: int,
    regressed_count: int,
    min_improved_runs: int,
    max_regressed_runs: int,
) -> str:
    if improved_count >= min_improved_runs and regressed_count <= max_regressed_runs:
        return "accepted_for_repeat_aware_search"
    return "blocked_by_stop_loss"


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _round_float(value: float) -> float:
    return round(float(value), 12)


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
