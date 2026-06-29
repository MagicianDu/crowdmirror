from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CROSS_PROVIDER_SCHEMA_VERSION = "lcdu-anes-llm-cross-provider-matrix-v1"
SEED_SCALE_REPEAT_SCHEMA_VERSION = "lcdu-anes-llm-seed-scale-repeat-matrix-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_llm_cross_provider_matrix(
    *,
    artifact_id: str,
    seed_scale_repeat_matrices: list[dict[str, Any]],
    min_provider_environment_count: int = 2,
) -> dict[str, Any]:
    for matrix in seed_scale_repeat_matrices:
        _validate_seed_scale_repeat_matrix(matrix)

    provider_summaries = [
        _provider_summary(matrix) for matrix in seed_scale_repeat_matrices
    ]
    provider_environment_count = len(
        {summary["provider_environment"] for summary in provider_summaries}
    )
    positive_provider_environment_count = len(
        {
            summary["provider_environment"]
            for summary in provider_summaries
            if summary["overall_status"] == "seed_scale_repeat_signal_positive"
        }
    )
    prompt_variant_stability = _prompt_variant_stability(provider_summaries)
    selected_prompt_variant = _selected_prompt_variant(
        prompt_variant_stability=prompt_variant_stability,
        provider_environment_count=provider_environment_count,
        min_provider_environment_count=min_provider_environment_count,
    )
    artifact = {
        "schema_version": CROSS_PROVIDER_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            provider_environment_count=provider_environment_count,
            positive_provider_environment_count=positive_provider_environment_count,
            min_provider_environment_count=min_provider_environment_count,
            selected_prompt_variant=selected_prompt_variant,
        ),
        "validation_type": "llm_cross_provider_stability_matrix",
        "min_provider_environment_count": min_provider_environment_count,
        "provider_environment_count": provider_environment_count,
        "positive_provider_environment_count": positive_provider_environment_count,
        "provider_environments": [
            summary["provider_environment"] for summary in provider_summaries
        ],
        "selected_prompt_variant": selected_prompt_variant,
        "prompt_variant_stability": prompt_variant_stability,
        "matrix_artifact_ids": [
            summary["artifact_id"] for summary in provider_summaries
        ],
        "provider_summaries": provider_summaries,
        "task_stability": _task_stability(provider_summaries),
        "llm_accounting": _llm_accounting(provider_summaries),
        "risk_flags": _risk_flags(
            provider_environment_count=provider_environment_count,
            positive_provider_environment_count=positive_provider_environment_count,
            min_provider_environment_count=min_provider_environment_count,
            provider_summaries=provider_summaries,
            selected_prompt_variant=selected_prompt_variant,
        ),
        "claim_boundary": (
            "This artifact checks whether LCDU prompt-variant seed/scale/repeat "
            "signals are directionally consistent across independent provider "
            "environments. It is not a strong-baseline comparison, production "
            "forecast, or full population-scale validation."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_llm_cross_provider_matrix(
    output: str | Path,
    *,
    artifact_id: str,
    matrix_artifact_paths: list[str | Path],
) -> dict[str, Any]:
    matrix = build_lcdu_anes_llm_cross_provider_matrix(
        artifact_id=artifact_id,
        seed_scale_repeat_matrices=[
            load_json_artifact(path) for path in matrix_artifact_paths
        ],
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"output_path": str(output_path), "artifact": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matrix-artifacts",
        nargs="+",
        required=True,
        help="Seed/scale/repeat matrix artifacts to aggregate.",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_llm_cross_provider/"
            "lcdu-anes-llm-cross-provider-matrix-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-llm-cross-provider-matrix-current-001",
    )
    args = parser.parse_args()
    written = write_lcdu_anes_llm_cross_provider_matrix(
        args.output,
        artifact_id=args.artifact_id,
        matrix_artifact_paths=args.matrix_artifacts,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": written["output_path"],
                "positive_provider_environment_count": artifact[
                    "positive_provider_environment_count"
                ],
                "provider_environment_count": artifact["provider_environment_count"],
                "status": artifact["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_seed_scale_repeat_matrix(matrix: dict[str, Any]) -> None:
    if matrix.get("schema_version") != SEED_SCALE_REPEAT_SCHEMA_VERSION:
        raise ValueError("seed_scale_repeat_matrix has unsupported schema_version")
    if matrix.get("validation_type") != "llm_seed_scale_repeat_matrix":
        raise ValueError("seed_scale_repeat_matrix has unsupported validation_type")
    if int(matrix.get("run_count", 0)) < 1:
        raise ValueError("seed_scale_repeat_matrix must include at least one run")


def _provider_summary(matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": matrix["artifact_id"],
        "provider": matrix.get("provider"),
        "model": matrix.get("model"),
        "base_url": matrix.get("base_url"),
        "provider_environment": _provider_environment(matrix),
        "overall_status": matrix.get("overall_status"),
        "run_count": matrix.get("run_count", 0),
        "positive_run_count": matrix.get("positive_run_count", 0),
        "prompt_variants": matrix.get("prompt_variants", []),
        "segment_scales": matrix.get("segment_scales", []),
        "segment_offsets": matrix.get("segment_offsets", []),
        "task_stability": matrix.get("task_stability", {}),
        "prompt_variant_stability": _matrix_prompt_variant_stability(matrix),
        "llm_accounting": matrix.get(
            "llm_accounting",
            {
                "total_call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "parse_failure_count": 0,
            },
        ),
    }


def _provider_environment(matrix: dict[str, Any]) -> str:
    base_url = matrix.get("base_url") or matrix.get("provider") or "unknown-provider"
    model = matrix.get("model") or "unknown-model"
    return f"{base_url}::{model}"


def _overall_status(
    *,
    provider_environment_count: int,
    positive_provider_environment_count: int,
    min_provider_environment_count: int,
    selected_prompt_variant: str | None,
) -> str:
    if provider_environment_count < min_provider_environment_count:
        return "cross_provider_evidence_insufficient"
    if positive_provider_environment_count == provider_environment_count:
        return "cross_provider_signal_positive"
    if selected_prompt_variant is not None:
        return "cross_provider_selected_variant_positive"
    if positive_provider_environment_count > 0:
        return "cross_provider_signal_mixed"
    return "cross_provider_signal_negative"


def _matrix_prompt_variant_stability(matrix: dict[str, Any]) -> dict[str, Any]:
    run_results = matrix.get("run_results")
    if not isinstance(run_results, list) or not run_results:
        return {}
    variants = sorted(
        {
            run.get("prompt_variant")
            for run in run_results
            if isinstance(run.get("prompt_variant"), str)
        }
    )
    stability = {}
    for variant in variants:
        variant_runs = [
            run for run in run_results if run.get("prompt_variant") == variant
        ]
        positive_count = sum(1 for run in variant_runs if _run_is_positive(run))
        stability[variant] = {
            "run_count": len(variant_runs),
            "positive_run_count": positive_count,
            "all_runs_positive": positive_count == len(variant_runs),
        }
    return stability


def _run_is_positive(run: dict[str, Any]) -> bool:
    if run.get("overall_status") != "cross_task_llm_signal_positive":
        return False
    task_summaries = run.get("task_summaries", {})
    if not isinstance(task_summaries, dict) or not task_summaries:
        return False
    for task_summary in task_summaries.values():
        if not task_summary.get("candidate_accepted"):
            return False
        if task_summary.get("test_final_loss", 0.0) >= task_summary.get(
            "test_initial_loss", 0.0
        ):
            return False
    return True


def _prompt_variant_stability(
    provider_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    variants = sorted(
        {
            variant
            for summary in provider_summaries
            for variant in summary.get("prompt_variant_stability", {})
        }
    )
    stability = {}
    for variant in variants:
        summaries = [
            summary
            for summary in provider_summaries
            if variant in summary.get("prompt_variant_stability", {})
        ]
        positive_count = sum(
            1
            for summary in summaries
            if summary["prompt_variant_stability"][variant]["all_runs_positive"]
        )
        provider_environment_count = len(
            {summary["provider_environment"] for summary in summaries}
        )
        stability[variant] = {
            "provider_environment_count": provider_environment_count,
            "positive_provider_environment_count": positive_count,
            "all_provider_environments_positive": (
                provider_environment_count > 0
                and positive_count == provider_environment_count
            ),
        }
    return stability


def _selected_prompt_variant(
    *,
    prompt_variant_stability: dict[str, Any],
    provider_environment_count: int,
    min_provider_environment_count: int,
) -> str | None:
    stable_variants = [
        variant
        for variant, stability in prompt_variant_stability.items()
        if stability["provider_environment_count"] >= min_provider_environment_count
        and stability["provider_environment_count"] == provider_environment_count
        and stability["all_provider_environments_positive"]
    ]
    if not stable_variants:
        return None
    if "deliberative" in stable_variants:
        return "deliberative"
    return stable_variants[0]


def _task_stability(provider_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    task_ids = sorted(
        {
            task_id
            for summary in provider_summaries
            for task_id in summary.get("task_stability", {})
        }
    )
    task_stability = {}
    for task_id in task_ids:
        summaries = [
            summary
            for summary in provider_summaries
            if task_id in summary.get("task_stability", {})
        ]
        positive_count = sum(
            1
            for summary in summaries
            if summary["overall_status"] == "seed_scale_repeat_signal_positive"
            and summary["task_stability"][task_id].get("test_improved_rate") == 1.0
        )
        task_stability[task_id] = {
            "provider_environment_count": len(
                {summary["provider_environment"] for summary in summaries}
            ),
            "positive_provider_environment_count": positive_count,
            "min_test_improved_rate": min(
                summary["task_stability"][task_id].get("test_improved_rate", 0.0)
                for summary in summaries
            ),
        }
    return task_stability


def _llm_accounting(provider_summaries: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_call_count": sum(
            summary["llm_accounting"]["total_call_count"]
            for summary in provider_summaries
        ),
        "total_input_tokens": sum(
            summary["llm_accounting"]["total_input_tokens"]
            for summary in provider_summaries
        ),
        "total_output_tokens": sum(
            summary["llm_accounting"]["total_output_tokens"]
            for summary in provider_summaries
        ),
        "parse_failure_count": sum(
            summary["llm_accounting"]["parse_failure_count"]
            for summary in provider_summaries
        ),
    }


def _risk_flags(
    *,
    provider_environment_count: int,
    positive_provider_environment_count: int,
    min_provider_environment_count: int,
    provider_summaries: list[dict[str, Any]],
    selected_prompt_variant: str | None,
) -> list[str]:
    flags = [
        "not_strong_baseline_matrix",
        "not_population_scale_validation",
    ]
    if provider_environment_count < min_provider_environment_count:
        flags.append("cross_provider_evidence_insufficient")
    if positive_provider_environment_count != provider_environment_count:
        flags.append("cross_provider_instability_observed")
    if selected_prompt_variant is not None and positive_provider_environment_count != (
        provider_environment_count
    ):
        flags.append("prompt_variant_selection_required")
    if any(
        summary["llm_accounting"].get("parse_failure_count", 0)
        for summary in provider_summaries
    ):
        flags.append("llm_parse_failure_observed")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES LLM cross-provider matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
