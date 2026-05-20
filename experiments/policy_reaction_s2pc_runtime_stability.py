from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


S2PC_RUNTIME_STABILITY_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-stability-v1"
S2PC_RUNTIME_EFFECT_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-effect-v1"
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"
S2PC_RUNTIME_STABILITY_CLAIM_BOUNDARY = (
    "S2PC runtime stability matrix is repeat evidence over local held-out "
    "public-data alignment, not field validation."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_runtime_stability_matrix(
    effect_artifacts: list[dict[str, Any]],
    *,
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    if not effect_artifacts:
        raise ValueError("stability matrix requires at least one effect artifact")
    for index, artifact in enumerate(effect_artifacts):
        _validate_effect_artifact(artifact, index=index, loss_metric=loss_metric)

    candidate_ids = {
        str(artifact["s2pc_candidate_id"]) for artifact in effect_artifacts
    }
    if len(candidate_ids) != 1:
        raise ValueError("S2PC runtime stability requires the same candidate_id")

    runs = [_run_summary(artifact) for artifact in effect_artifacts]
    improved_count = sum(1 for run in runs if run["overall_status"] == "improved")
    regressed_count = sum(1 for run in runs if run["overall_status"] == "regressed")
    no_change_count = sum(1 for run in runs if run["overall_status"] == "no_change")
    overall_status = _overall_status(
        effect_count=len(runs),
        improved_count=improved_count,
        regressed_count=regressed_count,
        no_change_count=no_change_count,
    )
    matrix = {
        "schema_version": S2PC_RUNTIME_STABILITY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "loss_metric": loss_metric,
        "effect_count": len(runs),
        "improved_count": improved_count,
        "regressed_count": regressed_count,
        "no_change_count": no_change_count,
        "candidate_ids": sorted(candidate_ids),
        "best_candidate_id": sorted(candidate_ids)[0],
        "model_ids": sorted({run["model"] for run in runs if run["model"]}),
        "scale_axes": _scale_axes(runs),
        "loss_summary": _loss_summary(runs),
        "runs": sorted(
            runs,
            key=lambda run: (
                run["scale"].get("persona_count", 0),
                run["scale"].get("seed", 0),
                run["product_runtime_run_id"],
            ),
        ),
        "risk_flags": _risk_flags(overall_status),
        "claim_boundary": S2PC_RUNTIME_STABILITY_CLAIM_BOUNDARY,
        "claim_boundaries": _claim_boundaries(effect_artifacts),
    }
    _assert_strict_json(matrix)
    return matrix


def write_policy_reaction_s2pc_runtime_stability_matrix(
    path: str | Path,
    *,
    effect_artifact_paths: list[str | Path],
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> Path:
    matrix = build_policy_reaction_s2pc_runtime_stability_matrix(
        [load_json_artifact(path) for path in effect_artifact_paths],
        artifact_id=artifact_id,
        loss_metric=loss_metric,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--effect-artifact",
        action="append",
        dest="effect_artifacts",
        required=True,
    )
    parser.add_argument(
        "--artifact-id",
        default=(
            "policy-reaction-s2pc-runtime-stability-gpt-oss-20b-"
            "calibration-split-c01-heldout-001"
        ),
    )
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-runtime-stability-gpt-oss-20b-"
            "calibration-split-c01-heldout-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_s2pc_runtime_stability_matrix(
        args.output,
        effect_artifact_paths=args.effect_artifacts,
        artifact_id=args.artifact_id,
        loss_metric=args.loss_metric,
    )
    matrix = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output_path),
                "status": matrix["overall_status"],
                "effect_count": matrix["effect_count"],
                "improved_count": matrix["improved_count"],
                "relative_loss_reduction_mean": matrix["loss_summary"][
                    "relative_loss_reduction_mean"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_effect_artifact(
    artifact: dict[str, Any],
    *,
    index: int,
    loss_metric: str,
) -> None:
    label = f"effect_artifacts[{index}]"
    if artifact.get("schema_version") != S2PC_RUNTIME_EFFECT_SCHEMA_VERSION:
        raise ValueError(f"{label} has unsupported schema_version")
    if artifact.get("loss_metric") != loss_metric:
        raise ValueError(f"{label} loss_metric must be {loss_metric}")
    for field_name in (
        "artifact_id",
        "overall_status",
        "baseline_loss",
        "s2pc_runtime_loss",
        "absolute_loss_delta",
        "relative_loss_reduction",
        "s2pc_candidate_id",
        "s2pc_product_run_id",
        "product_runtime_scale",
        "coverage",
        "source_split_contract",
    ):
        if field_name not in artifact:
            raise ValueError(f"{label} missing {field_name}")
    if artifact["source_split_contract"].get("runtime_effect_evaluation") != "heldout":
        raise ValueError(f"{label} must use held-out runtime effect evaluation")
    coverage = artifact["coverage"]
    if coverage.get("baseline_coverage_rate") != 1.0:
        raise ValueError(f"{label} baseline coverage must be complete")
    if coverage.get("s2pc_runtime_coverage_rate") != 1.0:
        raise ValueError(f"{label} S2PC runtime coverage must be complete")


def _run_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": artifact["artifact_id"],
        "overall_status": artifact["overall_status"],
        "candidate_id": artifact["s2pc_candidate_id"],
        "product_runtime_run_id": artifact["s2pc_product_run_id"],
        "model": artifact.get("product_runtime_model"),
        "scale": artifact["product_runtime_scale"],
        "baseline_loss": _round_float(artifact["baseline_loss"]),
        "s2pc_runtime_loss": _round_float(artifact["s2pc_runtime_loss"]),
        "absolute_loss_delta": _round_float(artifact["absolute_loss_delta"]),
        "relative_loss_reduction": _round_float(
            artifact["relative_loss_reduction"]
        ),
    }


def _scale_axes(runs: list[dict[str, Any]]) -> dict[str, list[int]]:
    return {
        "persona_counts": sorted(
            {
                int(run["scale"]["persona_count"])
                for run in runs
                if "persona_count" in run["scale"]
            }
        ),
        "scenario_counts": sorted(
            {
                int(run["scale"]["scenario_count"])
                for run in runs
                if "scenario_count" in run["scale"]
            }
        ),
        "seeds": sorted(
            {int(run["scale"]["seed"]) for run in runs if "seed" in run["scale"]}
        ),
    }


def _loss_summary(runs: list[dict[str, Any]]) -> dict[str, float]:
    relative_reductions = [run["relative_loss_reduction"] for run in runs]
    return {
        "baseline_loss_mean": _round_float(_mean([run["baseline_loss"] for run in runs])),
        "s2pc_runtime_loss_mean": _round_float(
            _mean([run["s2pc_runtime_loss"] for run in runs])
        ),
        "absolute_loss_delta_mean": _round_float(
            _mean([run["absolute_loss_delta"] for run in runs])
        ),
        "relative_loss_reduction_mean": _round_float(_mean(relative_reductions)),
        "relative_loss_reduction_min": _round_float(min(relative_reductions)),
        "relative_loss_reduction_max": _round_float(max(relative_reductions)),
    }


def _overall_status(
    *,
    effect_count: int,
    improved_count: int,
    regressed_count: int,
    no_change_count: int,
) -> str:
    if improved_count == effect_count:
        return "stable_improvement"
    if regressed_count == effect_count:
        return "stable_regression"
    if no_change_count == effect_count:
        return "stable_no_change"
    return "mixed"


def _risk_flags(overall_status: str) -> list[str]:
    flags = ["s2pc_runtime_stability_not_field_validation"]
    if overall_status != "stable_improvement":
        flags.append("s2pc_runtime_candidate_not_stable_across_repeats")
    return flags


def _claim_boundaries(effect_artifacts: list[dict[str, Any]]) -> list[str]:
    boundaries = [
        S2PC_RUNTIME_STABILITY_CLAIM_BOUNDARY,
        "All included runs must use held-out public-data alignment effect artifacts.",
        "The matrix summarizes local model repeat behavior for one fixed S2PC candidate and does not establish cross-source generalization.",
    ]
    for artifact in effect_artifacts:
        boundaries.extend(artifact.get("claim_boundaries", []))
    return _unique_strings([boundary for boundary in boundaries if boundary])


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)


def _round_float(value: float) -> float:
    return round(float(value), 12)


def _unique_strings(values: list[str]) -> list[str]:
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
