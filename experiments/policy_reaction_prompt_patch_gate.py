from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for path in (REPO_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from circe.calibration.prompt_patch import (  # noqa: E402
    PromptPatchCandidate,
    build_multi_candidate_prompt_patch_gate,
    generate_parameter_prompt_patches,
    generate_residual_prompt_patches,
)


POLICY_REACTION_PROMPT_PATCH_GATE_SCHEMA_VERSION = (
    "policy-reaction-prompt-patch-gate-v1"
)
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"
POLICY_REACTION_PROMPT_PATCH_CLAIM_BOUNDARY = (
    "Policy-reaction prompt/persona patch gate evidence only; candidates are "
    "generated from calibration split and accepted only on held-out evaluation."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_prompt_patch_candidate(
    calibration_benchmark: dict[str, Any],
    *,
    candidate_id: str,
    residual_threshold: float = 0.05,
    parameter_threshold: float = 0.05,
) -> PromptPatchCandidate:
    _validate_official_benchmark(calibration_benchmark, "calibration_benchmark")
    _require_source_split(
        calibration_benchmark,
        expected="calibration",
        label="candidate generation",
    )

    observed_by_segment = _distribution_by_segment(
        calibration_benchmark,
        field_name="official_distribution",
    )
    predicted_by_segment = _distribution_by_segment(
        calibration_benchmark,
        field_name="predicted_distribution",
    )
    residual_patches = generate_residual_prompt_patches(
        observed_by_segment=observed_by_segment,
        predicted_by_segment=predicted_by_segment,
        threshold=residual_threshold,
    )
    parameter_patches = generate_parameter_prompt_patches(
        segment_parameter_deltas=_parameter_deltas_by_segment(
            observed_by_segment=observed_by_segment,
            predicted_by_segment=predicted_by_segment,
        ),
        threshold=parameter_threshold,
    )
    patches = residual_patches + parameter_patches
    if not patches:
        raise ValueError("calibration benchmark produced no material prompt patches")

    return PromptPatchCandidate(
        candidate_id=candidate_id,
        generator="policy_reaction_residual_parameter",
        rationale=(
            "HPS/HTOPS calibration split residuals produce segment prompt patches "
            "and persona-level calibration anchor deltas."
        ),
        patches=patches,
        source_split="calibration",
        metadata={
            "calibration_benchmark_artifact_id": calibration_benchmark["artifact_id"],
            "calibration_prediction_artifact_id": calibration_benchmark.get(
                "prediction_artifact_id"
            ),
            "calibration_source_ingestion_artifact_id": calibration_benchmark.get(
                "source_ingestion_artifact_id"
            ),
            "residual_patch_count": len(residual_patches),
            "parameter_patch_count": len(parameter_patches),
            "residual_threshold": residual_threshold,
            "parameter_threshold": parameter_threshold,
        },
    )


def build_policy_reaction_prompt_patch_gate(
    calibration_benchmark: dict[str, Any],
    initial_heldout_benchmark: dict[str, Any],
    candidate_heldout_benchmark: dict[str, Any],
    *,
    artifact_id: str,
    candidate_id: str = "policy-reaction-calibration-split-candidate",
    loss_metric: str = DEFAULT_LOSS_METRIC,
    residual_threshold: float = 0.05,
    parameter_threshold: float = 0.05,
    prompt_components: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_official_benchmark(initial_heldout_benchmark, "initial_heldout_benchmark")
    _validate_official_benchmark(
        candidate_heldout_benchmark,
        "candidate_heldout_benchmark",
    )
    _require_source_split(
        initial_heldout_benchmark,
        expected="heldout",
        label="initial benchmark",
    )
    _require_source_split(
        candidate_heldout_benchmark,
        expected="heldout",
        label="candidate acceptance",
    )

    candidate = build_policy_reaction_prompt_patch_candidate(
        calibration_benchmark,
        candidate_id=candidate_id,
        residual_threshold=residual_threshold,
        parameter_threshold=parameter_threshold,
    )
    prompt_components = prompt_components or _default_prompt_components(
        calibration_benchmark
    )
    gate = build_multi_candidate_prompt_patch_gate(
        prompt_components,
        [candidate],
        artifact_id=artifact_id,
        initial_loss=_benchmark_loss(initial_heldout_benchmark, loss_metric),
        candidate_evaluations={
            candidate.candidate_id: {
                "loss": _benchmark_loss(candidate_heldout_benchmark, loss_metric),
                "coverage_rate": _coverage_rate(candidate_heldout_benchmark),
                "evaluation_split": "heldout",
                "benchmark_artifact_id": candidate_heldout_benchmark["artifact_id"],
            }
        },
    )
    prompt_patch_gate_schema_version = gate["schema_version"]
    gate.update(
        {
            "schema_version": POLICY_REACTION_PROMPT_PATCH_GATE_SCHEMA_VERSION,
            "prompt_patch_gate_schema_version": prompt_patch_gate_schema_version,
            "calibration_benchmark_artifact_id": calibration_benchmark["artifact_id"],
            "initial_heldout_benchmark_artifact_id": initial_heldout_benchmark[
                "artifact_id"
            ],
            "candidate_heldout_benchmark_artifact_id": candidate_heldout_benchmark[
                "artifact_id"
            ],
            "initial_prediction_artifact_id": initial_heldout_benchmark.get(
                "prediction_artifact_id"
            ),
            "candidate_prediction_artifact_id": candidate_heldout_benchmark.get(
                "prediction_artifact_id"
            ),
            "loss_metric": loss_metric,
            "source_split_contract": {
                "candidate_generation": "calibration",
                "candidate_acceptance": "heldout",
            },
            "claim_boundary": POLICY_REACTION_PROMPT_PATCH_CLAIM_BOUNDARY,
            "claim_boundaries": [
                POLICY_REACTION_PROMPT_PATCH_CLAIM_BOUNDARY,
                "Prompt/persona patch candidates are generated only from the "
                "HPS/HTOPS calibration projection.",
                "The acceptance decision uses only the held-out HPS/HTOPS "
                "evaluation projection and does not establish field validation.",
            ],
        }
    )
    _assert_strict_json(gate)
    return gate


def write_policy_reaction_prompt_patch_gate(
    path: str | Path,
    *,
    calibration_benchmark_path: str | Path,
    initial_heldout_benchmark_path: str | Path,
    candidate_heldout_benchmark_path: str | Path,
    artifact_id: str,
    candidate_id: str = "policy-reaction-calibration-split-candidate",
    loss_metric: str = DEFAULT_LOSS_METRIC,
    residual_threshold: float = 0.05,
    parameter_threshold: float = 0.05,
) -> Path:
    artifact = build_policy_reaction_prompt_patch_gate(
        load_json_artifact(calibration_benchmark_path),
        load_json_artifact(initial_heldout_benchmark_path),
        load_json_artifact(candidate_heldout_benchmark_path),
        artifact_id=artifact_id,
        candidate_id=candidate_id,
        loss_metric=loss_metric,
        residual_threshold=residual_threshold,
        parameter_threshold=parameter_threshold,
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
        "--calibration-benchmark",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-"
            "calibration-split-initial-001.json"
        ),
    )
    parser.add_argument(
        "--initial-heldout-benchmark",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-"
            "heldout-001.json"
        ),
    )
    parser.add_argument(
        "--candidate-heldout-benchmark",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-"
            "calibration-split-heldout-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default=(
            "policy-reaction-prompt-patch-gate-gpt-oss-20b-12x3-"
            "calibration-split-heldout-001"
        ),
    )
    parser.add_argument(
        "--candidate-id",
        default="policy-reaction-calibration-split-residual-parameter-candidate",
    )
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    parser.add_argument("--residual-threshold", type=float, default=0.05)
    parser.add_argument("--parameter-threshold", type=float, default=0.05)
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-prompt-patch-gate-gpt-oss-20b-12x3-"
            "calibration-split-heldout-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_prompt_patch_gate(
        args.output,
        calibration_benchmark_path=args.calibration_benchmark,
        initial_heldout_benchmark_path=args.initial_heldout_benchmark,
        candidate_heldout_benchmark_path=args.candidate_heldout_benchmark,
        artifact_id=args.artifact_id,
        candidate_id=args.candidate_id,
        loss_metric=args.loss_metric,
        residual_threshold=args.residual_threshold,
        parameter_threshold=args.parameter_threshold,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output_path),
                "status": "passed",
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _distribution_by_segment(
    benchmark: dict[str, Any],
    *,
    field_name: str,
) -> dict[str, dict[str, float]]:
    return {
        segment: _policy_distribution(metric[field_name], f"{segment}.{field_name}")
        for segment, metric in sorted(benchmark["segment_metrics"].items())
    }


def _parameter_deltas_by_segment(
    *,
    observed_by_segment: dict[str, dict[str, float]],
    predicted_by_segment: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    deltas = {}
    for segment, observed in sorted(observed_by_segment.items()):
        predicted = predicted_by_segment.get(segment, {})
        segment_deltas = {}
        for policy_id in sorted(set(observed) | set(predicted)):
            parameter = f"{policy_id}_bias"
            segment_deltas[parameter] = observed.get(policy_id, 0.0) - predicted.get(
                policy_id,
                0.0,
            )
        deltas[segment] = segment_deltas
    return deltas


def _default_prompt_components(calibration_benchmark: dict[str, Any]) -> dict[str, Any]:
    segments = sorted(calibration_benchmark["segment_metrics"])
    return {
        "global_instruction": (
            "Simulate policy reaction probabilities for public-use HPS/HTOPS "
            "food-cost segments."
        ),
        "segment_prompt": {
            segment: f"Segment {segment}: use persona-specific policy sensitivities."
            for segment in segments
        },
        "persona_prompt": {},
        "policy_interpretation_prompt": {
            "food_cost_policy": (
                "Compare baseline/no new support, cash cost-of-living rebate, "
                "and food subsidy expansion as policy reaction alternatives."
            )
        },
        "calibration_anchor": {
            segment: "No accepted calibration patch has been applied."
            for segment in segments
        },
        "response_contract": (
            "Return strict JSON probabilities over baseline_no_new_support, "
            "cash_cost_of_living_rebate, and food_subsidy_expansion."
        ),
    }


def _validate_official_benchmark(artifact: dict[str, Any], label: str) -> None:
    if artifact.get("schema_version") != "policy-reaction-official-segment-benchmark-v1":
        raise ValueError(f"{label} has unsupported schema_version")
    if not artifact.get("artifact_id"):
        raise ValueError(f"{label} missing artifact_id")
    if not isinstance(artifact.get("segment_metrics"), dict):
        raise ValueError(f"{label} missing segment_metrics")


def _require_source_split(
    artifact: dict[str, Any],
    *,
    expected: str,
    label: str,
) -> None:
    actual = _source_split(artifact)
    if actual != expected:
        if expected == "heldout":
            raise ValueError(f"{label} must use held-out evaluation split")
        raise ValueError(f"{label} must use {expected} split")


def _source_split(artifact: dict[str, Any]) -> str:
    source = str(artifact.get("source_ingestion_artifact_id", "")).lower()
    if "calibration" in source:
        return "calibration"
    if "evaluation" in source or "heldout" in source or "held-out" in source:
        return "heldout"
    return "unknown"


def _benchmark_loss(artifact: dict[str, Any], loss_metric: str) -> float:
    metrics = artifact.get("benchmark_metrics", {})
    value = metrics.get(loss_metric)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"benchmark missing numeric {loss_metric}")
    return float(value)


def _coverage_rate(artifact: dict[str, Any]) -> float:
    value = artifact.get("segment_coverage", {}).get("coverage_rate")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _policy_distribution(raw: dict[str, Any], context: str) -> dict[str, float]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{context} must be a non-empty object")
    values = {}
    for policy_id, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"{context} probabilities must be numeric")
        values[str(policy_id)] = float(value)
    return values


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
