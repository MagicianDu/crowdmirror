from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


S2PC_RUNTIME_EFFECT_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-effect-v1"
S2PC_RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION = (
    "policy-reaction-s2pc-runtime-effect-matrix-v1"
)
OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION = (
    "policy-reaction-official-segment-benchmark-v1"
)
S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
PRODUCT_COHORT_MANIFEST_SCHEMA_VERSION = "crowdmirror-llm-cohort-gate-v1"
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"
S2PC_RUNTIME_EFFECT_CLAIM_BOUNDARY = (
    "S2PC runtime effect is a held-out public-data alignment comparison; "
    "not field validation."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_runtime_effect(
    *,
    baseline_heldout_benchmark: dict[str, Any],
    baseline_product_manifest: dict[str, Any],
    s2pc_runtime_heldout_benchmark: dict[str, Any],
    s2pc_product_manifest: dict[str, Any],
    s2pc_candidate: dict[str, Any],
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    _validate_official_heldout_benchmark(
        baseline_heldout_benchmark,
        label="baseline_heldout_benchmark",
    )
    _validate_official_heldout_benchmark(
        s2pc_runtime_heldout_benchmark,
        label="s2pc_runtime_heldout_benchmark",
    )
    _validate_same_heldout_target(
        baseline_heldout_benchmark,
        s2pc_runtime_heldout_benchmark,
    )
    _validate_product_manifest(
        baseline_product_manifest,
        label="baseline_product_manifest",
        require_s2pc=False,
    )
    _validate_product_manifest(
        s2pc_product_manifest,
        label="s2pc_product_manifest",
        require_s2pc=True,
    )
    if baseline_product_manifest["scale"] != s2pc_product_manifest["scale"]:
        raise ValueError("baseline and S2PC Product manifests must use the same scale")
    _validate_s2pc_candidate(s2pc_candidate)

    baseline_loss = _benchmark_loss(baseline_heldout_benchmark, loss_metric)
    s2pc_runtime_loss = _benchmark_loss(s2pc_runtime_heldout_benchmark, loss_metric)
    absolute_delta = _round_float(baseline_loss - s2pc_runtime_loss)
    relative_reduction = (
        _round_float(absolute_delta / baseline_loss) if baseline_loss > 0 else None
    )
    overall_status = _overall_status(absolute_delta)
    artifact = {
        "schema_version": S2PC_RUNTIME_EFFECT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "loss_metric": loss_metric,
        "baseline_loss": _round_float(baseline_loss),
        "s2pc_runtime_loss": _round_float(s2pc_runtime_loss),
        "absolute_loss_delta": absolute_delta,
        "relative_loss_reduction": relative_reduction,
        "baseline_heldout_benchmark_artifact_id": baseline_heldout_benchmark[
            "artifact_id"
        ],
        "s2pc_runtime_heldout_benchmark_artifact_id": (
            s2pc_runtime_heldout_benchmark["artifact_id"]
        ),
        "baseline_prediction_artifact_id": baseline_heldout_benchmark.get(
            "prediction_artifact_id"
        ),
        "s2pc_runtime_prediction_artifact_id": (
            s2pc_runtime_heldout_benchmark.get("prediction_artifact_id")
        ),
        "heldout_source_ingestion_artifact_id": baseline_heldout_benchmark[
            "source_ingestion_artifact_id"
        ],
        "baseline_product_run_id": baseline_product_manifest["run_id"],
        "s2pc_product_run_id": s2pc_product_manifest["run_id"],
        "product_runtime_model": _product_model(s2pc_product_manifest),
        "product_runtime_scale": s2pc_product_manifest["scale"],
        "s2pc_candidate_id": s2pc_candidate["candidate_id"],
        "s2pc_candidate_artifact_id": s2pc_candidate["candidate_id"],
        "source_split_contract": {
            **s2pc_candidate["source_split_contract"],
            "runtime_effect_evaluation": "heldout",
        },
        "coverage": {
            "baseline_coverage_rate": _coverage_rate(baseline_heldout_benchmark),
            "s2pc_runtime_coverage_rate": _coverage_rate(
                s2pc_runtime_heldout_benchmark
            ),
        },
        "risk_flags": _risk_flags(overall_status),
        "claim_boundary": S2PC_RUNTIME_EFFECT_CLAIM_BOUNDARY,
        "claim_boundaries": _claim_boundaries(
            baseline_heldout_benchmark,
            s2pc_runtime_heldout_benchmark,
            s2pc_candidate,
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_s2pc_runtime_effect(
    path: str | Path,
    *,
    baseline_heldout_benchmark_path: str | Path,
    baseline_product_manifest_path: str | Path,
    s2pc_runtime_heldout_benchmark_path: str | Path,
    s2pc_product_manifest_path: str | Path,
    s2pc_candidate_path: str | Path,
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> Path:
    artifact = build_policy_reaction_s2pc_runtime_effect(
        baseline_heldout_benchmark=load_json_artifact(
            baseline_heldout_benchmark_path
        ),
        baseline_product_manifest=load_json_artifact(baseline_product_manifest_path),
        s2pc_runtime_heldout_benchmark=load_json_artifact(
            s2pc_runtime_heldout_benchmark_path
        ),
        s2pc_product_manifest=load_json_artifact(s2pc_product_manifest_path),
        s2pc_candidate=load_json_artifact(s2pc_candidate_path),
        artifact_id=artifact_id,
        loss_metric=loss_metric,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def build_policy_reaction_s2pc_runtime_effect_matrix(
    effect_artifacts: list[dict[str, Any]],
    *,
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    if not effect_artifacts:
        raise ValueError("effect_artifacts must not be empty")
    validated_effects = []
    for artifact in effect_artifacts:
        _validate_runtime_effect_artifact(artifact, loss_metric=loss_metric)
        validated_effects.append(artifact)

    sorted_effects = sorted(
        validated_effects,
        key=lambda artifact: (
            float(artifact["s2pc_runtime_loss"]),
            str(artifact["s2pc_candidate_id"]),
        ),
    )
    improved_count = sum(
        1 for artifact in sorted_effects if artifact["overall_status"] == "improved"
    )
    regressed_count = sum(
        1 for artifact in sorted_effects if artifact["overall_status"] == "regressed"
    )
    no_change_count = sum(
        1 for artifact in sorted_effects if artifact["overall_status"] == "no_change"
    )
    best = sorted_effects[0]
    matrix = {
        "schema_version": S2PC_RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _matrix_overall_status(
            candidate_count=len(sorted_effects),
            improved_count=improved_count,
            regressed_count=regressed_count,
        ),
        "loss_metric": loss_metric,
        "candidate_count": len(sorted_effects),
        "improved_count": improved_count,
        "regressed_count": regressed_count,
        "no_change_count": no_change_count,
        "best_candidate_id": best["s2pc_candidate_id"],
        "best_s2pc_runtime_loss": _round_float(best["s2pc_runtime_loss"]),
        "best_relative_loss_reduction": _round_float(
            best["relative_loss_reduction"]
        )
        if best.get("relative_loss_reduction") is not None
        else None,
        "candidate_results": [
            {
                "artifact_id": artifact["artifact_id"],
                "overall_status": artifact["overall_status"],
                "s2pc_candidate_id": artifact["s2pc_candidate_id"],
                "s2pc_product_run_id": artifact["s2pc_product_run_id"],
                "baseline_loss": _round_float(artifact["baseline_loss"]),
                "s2pc_runtime_loss": _round_float(artifact["s2pc_runtime_loss"]),
                "absolute_loss_delta": _round_float(artifact["absolute_loss_delta"]),
                "relative_loss_reduction": (
                    _round_float(artifact["relative_loss_reduction"])
                    if artifact.get("relative_loss_reduction") is not None
                    else None
                ),
            }
            for artifact in sorted_effects
        ],
        "claim_boundary": (
            "S2PC runtime effect matrix ranks held-out alignment outcomes across "
            "candidate variants; not field validation."
        ),
        "claim_boundaries": _unique_strings(
            [
                "This matrix compares held-out alignment across multiple S2PC runtime candidates.",
                "Only candidates with lower held-out loss than baseline count as improvements.",
                *[
                    boundary
                    for artifact in sorted_effects
                    for boundary in artifact.get("claim_boundaries", [])
                ],
            ]
        ),
    }
    _assert_strict_json(matrix)
    return matrix


def write_policy_reaction_s2pc_runtime_effect_matrix(
    path: str | Path,
    *,
    effect_artifact_paths: list[str | Path],
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> Path:
    artifact = build_policy_reaction_s2pc_runtime_effect_matrix(
        [load_json_artifact(effect_path) for effect_path in effect_artifact_paths],
        artifact_id=artifact_id,
        loss_metric=loss_metric,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["effect", "matrix"],
        default="effect",
    )
    parser.add_argument("--baseline-heldout-benchmark")
    parser.add_argument("--baseline-product-manifest")
    parser.add_argument("--s2pc-runtime-heldout-benchmark")
    parser.add_argument("--s2pc-product-manifest")
    parser.add_argument("--s2pc-candidate")
    parser.add_argument("--effect-artifact", action="append", default=[])
    parser.add_argument(
        "--artifact-id",
        default=(
            "policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-"
            "calibration-split-heldout-001"
        ),
    )
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-"
            "calibration-split-heldout-001.json"
        ),
    )
    args = parser.parse_args()
    if args.mode == "matrix":
        if not args.effect_artifact:
            raise ValueError("matrix mode requires at least one --effect-artifact")
        output_path = write_policy_reaction_s2pc_runtime_effect_matrix(
            args.output,
            effect_artifact_paths=args.effect_artifact,
            artifact_id=args.artifact_id,
            loss_metric=args.loss_metric,
        )
        artifact = load_json_artifact(output_path)
        print(
            json.dumps(
                {
                    "artifact_id": args.artifact_id,
                    "output": str(output_path),
                    "status": artifact["overall_status"],
                    "candidate_count": artifact["candidate_count"],
                    "best_candidate_id": artifact["best_candidate_id"],
                    "best_s2pc_runtime_loss": artifact["best_s2pc_runtime_loss"],
                },
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0

    required_args = {
        "baseline_heldout_benchmark": args.baseline_heldout_benchmark,
        "baseline_product_manifest": args.baseline_product_manifest,
        "s2pc_runtime_heldout_benchmark": args.s2pc_runtime_heldout_benchmark,
        "s2pc_product_manifest": args.s2pc_product_manifest,
        "s2pc_candidate": args.s2pc_candidate,
    }
    missing = [name for name, value in required_args.items() if not value]
    if missing:
        raise ValueError(
            "effect mode missing required arguments: " + ", ".join(missing)
        )

    output_path = write_policy_reaction_s2pc_runtime_effect(
        args.output,
        baseline_heldout_benchmark_path=args.baseline_heldout_benchmark,
        baseline_product_manifest_path=args.baseline_product_manifest,
        s2pc_runtime_heldout_benchmark_path=args.s2pc_runtime_heldout_benchmark,
        s2pc_product_manifest_path=args.s2pc_product_manifest,
        s2pc_candidate_path=args.s2pc_candidate,
        artifact_id=args.artifact_id,
        loss_metric=args.loss_metric,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output_path),
                "status": artifact["overall_status"],
                "baseline_loss": artifact["baseline_loss"],
                "s2pc_runtime_loss": artifact["s2pc_runtime_loss"],
                "relative_loss_reduction": artifact["relative_loss_reduction"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_official_heldout_benchmark(artifact: dict[str, Any], *, label: str) -> None:
    if artifact.get("schema_version") != OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION:
        raise ValueError(f"{label} has unsupported schema_version")
    if artifact.get("overall_status") != "passed":
        raise ValueError(f"{label} must be passed")
    for field_name in (
        "artifact_id",
        "source_ingestion_artifact_id",
        "prediction_artifact_id",
        "benchmark_metrics",
        "segment_coverage",
    ):
        if field_name not in artifact:
            raise ValueError(f"{label} missing {field_name}")
    if _source_split(artifact) != "heldout":
        raise ValueError(f"{label} must use held-out evaluation split")
    if _coverage_rate(artifact) < 1.0:
        raise ValueError(f"{label} must have complete segment coverage")


def _validate_same_heldout_target(baseline: dict[str, Any], s2pc: dict[str, Any]) -> None:
    if baseline["source_ingestion_artifact_id"] != s2pc[
        "source_ingestion_artifact_id"
    ]:
        raise ValueError("S2PC runtime comparison requires the same held-out target")


def _validate_product_manifest(
    manifest: dict[str, Any],
    *,
    label: str,
    require_s2pc: bool,
) -> None:
    if manifest.get("schema_version") != PRODUCT_COHORT_MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"{label} has unsupported schema_version")
    if manifest.get("status") != "completed":
        raise ValueError(f"{label} must be completed")
    if not manifest.get("run_id"):
        raise ValueError(f"{label} missing run_id")
    if not isinstance(manifest.get("scale"), dict):
        raise ValueError(f"{label} missing scale")
    has_s2pc = "s2pc_context" in manifest or "s2pc_context" in manifest.get(
        "report",
        {},
    )
    if require_s2pc and not has_s2pc:
        raise ValueError(f"{label} must include s2pc_context")
    if not require_s2pc and has_s2pc:
        raise ValueError(f"{label} must not include s2pc_context")


def _validate_s2pc_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("s2pc_candidate has unsupported schema_version")
    for field_name in (
        "candidate_id",
        "generator",
        "source_split_contract",
        "candidate_prompt_components",
    ):
        if field_name not in candidate:
            raise ValueError(f"s2pc_candidate missing {field_name}")
    contract = candidate["source_split_contract"]
    if contract.get("residual_mining") != "calibration":
        raise ValueError("S2PC residual mining must use calibration")
    if contract.get("semantic_factor_retrieval") != "calibration":
        raise ValueError("S2PC factor retrieval must use calibration")
    if contract.get("parameter_search") != "calibration":
        raise ValueError("S2PC parameter search must use calibration")
    if contract.get("candidate_acceptance") != "heldout_required":
        raise ValueError("S2PC candidate must require heldout acceptance")


def _validate_runtime_effect_artifact(
    artifact: dict[str, Any], loss_metric: str
) -> None:
    if artifact.get("schema_version") != S2PC_RUNTIME_EFFECT_SCHEMA_VERSION:
        raise ValueError("runtime effect artifact has unsupported schema_version")
    if artifact.get("loss_metric") != loss_metric:
        raise ValueError("runtime effect artifact uses unexpected loss_metric")
    for field_name in (
        "artifact_id",
        "overall_status",
        "baseline_loss",
        "s2pc_runtime_loss",
        "absolute_loss_delta",
        "s2pc_candidate_id",
        "s2pc_product_run_id",
    ):
        if field_name not in artifact:
            raise ValueError(f"runtime effect artifact missing {field_name}")
    if artifact["overall_status"] not in {"improved", "regressed", "no_change"}:
        raise ValueError("runtime effect artifact has unsupported overall_status")


def _matrix_overall_status(
    *, candidate_count: int, improved_count: int, regressed_count: int
) -> str:
    if improved_count > 0:
        return "candidate_improvements_available"
    if regressed_count == candidate_count:
        return "all_candidates_regressed"
    return "no_candidate_improvement"


def _benchmark_loss(artifact: dict[str, Any], loss_metric: str) -> float:
    value = artifact.get("benchmark_metrics", {}).get(loss_metric)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"benchmark missing numeric {loss_metric}")
    return float(value)


def _coverage_rate(artifact: dict[str, Any]) -> float:
    value = artifact.get("segment_coverage", {}).get("coverage_rate")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _source_split(artifact: dict[str, Any]) -> str:
    source = str(artifact.get("source_ingestion_artifact_id", "")).lower()
    if "evaluation" in source or "heldout" in source or "held-out" in source:
        return "heldout"
    if "calibration" in source:
        return "calibration"
    return "unknown"


def _product_model(manifest: dict[str, Any]) -> Any:
    return manifest.get("llm_accounting", {}).get("model") or manifest.get(
        "report",
        {},
    ).get("llm_accounting", {}).get("model")


def _overall_status(absolute_delta: float) -> str:
    if absolute_delta > 0:
        return "improved"
    if absolute_delta < 0:
        return "regressed"
    return "no_change"


def _risk_flags(overall_status: str) -> list[str]:
    flags = ["s2pc_runtime_effect_not_field_validation"]
    if overall_status != "improved":
        flags.append("s2pc_runtime_did_not_improve_heldout_alignment")
    return flags


def _claim_boundaries(
    baseline_heldout_benchmark: dict[str, Any],
    s2pc_runtime_heldout_benchmark: dict[str, Any],
    s2pc_candidate: dict[str, Any],
) -> list[str]:
    boundaries = [
        S2PC_RUNTIME_EFFECT_CLAIM_BOUNDARY,
        "The baseline and S2PC runtime benchmarks use the same held-out "
        "HPS/HTOPS evaluation projection.",
        "This artifact compares segment-level distributional alignment only; it "
        "does not establish causal policy effects.",
    ]
    boundaries.extend(baseline_heldout_benchmark.get("claim_boundaries", []))
    boundaries.extend(s2pc_runtime_heldout_benchmark.get("claim_boundaries", []))
    boundary = s2pc_candidate.get("claim_boundary")
    if isinstance(boundary, str):
        boundaries.append(boundary)
    return _unique_strings([boundary for boundary in boundaries if boundary])


def _unique_strings(values: list[str]) -> list[str]:
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _round_float(value: float) -> float:
    return round(float(value), 12)


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
