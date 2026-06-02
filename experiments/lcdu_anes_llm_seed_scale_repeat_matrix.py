from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from circe.llm_client import LLMResponse  # noqa: E402
from experiments.lcdu_anes_llm_simulator_validation import (  # noqa: E402
    _build_completion_fn,
    build_lcdu_anes_llm_simulator_validation_artifact,
    build_blocked_llm_simulator_artifact,
    load_json_artifact,
)


MATRIX_SCHEMA_VERSION = "lcdu-anes-llm-seed-scale-repeat-matrix-v1"
CompletionFn = Callable[[str, str], LLMResponse]


def build_lcdu_anes_llm_seed_scale_repeat_matrix(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    completion_fn: CompletionFn,
    segment_scales: list[int],
    segment_offsets: list[int],
    prompt_variants: list[str],
) -> dict[str, Any]:
    run_results = []
    for segment_scale in segment_scales:
        for segment_offset in segment_offsets:
            for prompt_variant in prompt_variants:
                run_id = (
                    f"{artifact_id}-scale{segment_scale}-offset{segment_offset}-"
                    f"{prompt_variant}"
                )
                run_artifact = build_lcdu_anes_llm_simulator_validation_artifact(
                    microdata_artifact=microdata_artifact,
                    artifact_id=run_id,
                    provider=provider,
                    model=model,
                    base_url=base_url,
                    completion_fn=completion_fn,
                    max_segments_per_task=segment_scale,
                    segment_offset=segment_offset,
                    prompt_variant=prompt_variant,
                )
                run_results.append(_summarize_run(run_artifact))
    matrix = _build_matrix_artifact(
        artifact_id=artifact_id,
        source_artifact_id=microdata_artifact["artifact_id"],
        provider=provider,
        model=model,
        base_url=base_url,
        segment_scales=segment_scales,
        segment_offsets=segment_offsets,
        prompt_variants=prompt_variants,
        run_results=run_results,
    )
    _assert_strict_json(matrix)
    return matrix


def build_blocked_seed_scale_repeat_matrix(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    error: Exception,
) -> dict[str, Any]:
    blocked = build_blocked_llm_simulator_artifact(
        microdata_artifact=microdata_artifact,
        artifact_id=f"{artifact_id}-blocked-run",
        provider=provider,
        model=model,
        base_url=base_url,
        error=error,
    )
    matrix = _build_matrix_artifact(
        artifact_id=artifact_id,
        source_artifact_id=microdata_artifact.get("artifact_id"),
        provider=provider,
        model=model,
        base_url=base_url,
        segment_scales=[],
        segment_offsets=[],
        prompt_variants=[],
        run_results=[_summarize_run(blocked)],
    )
    matrix["overall_status"] = "blocked_provider_unavailable"
    matrix["risk_flags"].append("provider_unavailable")
    _assert_strict_json(matrix)
    return matrix


def write_lcdu_anes_llm_seed_scale_repeat_matrix(
    output: str | Path,
    *,
    microdata_artifact_path: str | Path,
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    segment_scales: list[int],
    segment_offsets: list[int],
    prompt_variants: list[str],
    execute: bool,
) -> dict[str, Any]:
    microdata_artifact = load_json_artifact(microdata_artifact_path)
    if execute:
        completion_fn = _build_completion_fn(
            provider=provider,
            model=model,
            base_url=base_url,
        )
        try:
            matrix = build_lcdu_anes_llm_seed_scale_repeat_matrix(
                microdata_artifact=microdata_artifact,
                artifact_id=artifact_id,
                provider=provider,
                model=model,
                base_url=base_url,
                completion_fn=completion_fn,
                segment_scales=segment_scales,
                segment_offsets=segment_offsets,
                prompt_variants=prompt_variants,
            )
        except Exception as exc:
            matrix = build_blocked_seed_scale_repeat_matrix(
                microdata_artifact=microdata_artifact,
                artifact_id=artifact_id,
                provider=provider,
                model=model,
                base_url=base_url,
                error=exc,
            )
    else:
        matrix = _planned_matrix(
            microdata_artifact=microdata_artifact,
            artifact_id=artifact_id,
            provider=provider,
            model=model,
            base_url=base_url,
            segment_scales=segment_scales,
            segment_offsets=segment_offsets,
            prompt_variants=prompt_variants,
        )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"output_path": str(output_path), "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--microdata-artifact",
        default=(
            "experiments/results/lcdu_public_task_microdata/"
            "lcdu-anes-2024-sda-public-microdata-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_llm_seed_scale_repeat/"
            "lcdu-anes-llm-seed-scale-repeat-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-llm-seed-scale-repeat-current-001",
    )
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--segment-scales", nargs="+", type=int, default=[2, 4])
    parser.add_argument("--segment-offsets", nargs="+", type=int, default=[0, 1])
    parser.add_argument(
        "--prompt-variants",
        nargs="+",
        choices=["standard", "compact", "deliberative"],
        default=["standard"],
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    written = write_lcdu_anes_llm_seed_scale_repeat_matrix(
        args.output,
        microdata_artifact_path=args.microdata_artifact,
        artifact_id=args.artifact_id,
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        segment_scales=args.segment_scales,
        segment_offsets=args.segment_offsets,
        prompt_variants=args.prompt_variants,
        execute=args.execute,
    )
    matrix = written["matrix"]
    print(
        json.dumps(
            {
                "artifact_id": matrix["artifact_id"],
                "output": written["output_path"],
                "positive_run_count": matrix["positive_run_count"],
                "run_count": matrix["run_count"],
                "status": matrix["overall_status"],
                "total_call_count": matrix["llm_accounting"]["total_call_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _build_matrix_artifact(
    *,
    artifact_id: str,
    source_artifact_id: str | None,
    provider: str,
    model: str,
    base_url: str | None,
    segment_scales: list[int],
    segment_offsets: list[int],
    prompt_variants: list[str],
    run_results: list[dict[str, Any]],
) -> dict[str, Any]:
    run_count = len(run_results)
    positive_run_count = sum(
        1 for result in run_results if result["overall_status"] == "cross_task_llm_signal_positive"
    )
    task_stability = _task_stability(run_results)
    total_call_count = sum(
        result["llm_accounting"]["total_call_count"] for result in run_results
    )
    total_input_tokens = sum(
        result["llm_accounting"]["total_input_tokens"] for result in run_results
    )
    total_output_tokens = sum(
        result["llm_accounting"]["total_output_tokens"] for result in run_results
    )
    parse_failure_count = sum(
        result["llm_accounting"]["parse_failure_count"] for result in run_results
    )
    return {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _matrix_status(
            run_count=run_count,
            positive_run_count=positive_run_count,
            parse_failure_count=parse_failure_count,
        ),
        "source_artifact_id": source_artifact_id,
        "validation_type": "llm_seed_scale_repeat_matrix",
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "segment_scales": segment_scales,
        "segment_offsets": segment_offsets,
        "prompt_variants": prompt_variants,
        "run_count": run_count,
        "positive_run_count": positive_run_count,
        "task_stability": task_stability,
        "llm_accounting": {
            "total_call_count": total_call_count,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "parse_failure_count": parse_failure_count,
        },
        "run_results": run_results,
        "risk_flags": _risk_flags(
            run_count=run_count,
            positive_run_count=positive_run_count,
            parse_failure_count=parse_failure_count,
        ),
        "claim_boundary": (
            "This matrix tests whether the ANES LLM simulator signal is stable "
            "across small segment scales, segment offsets, and prompt variants. "
            "It is still not a strong-baseline matrix, cross-provider proof, or "
            "population-scale validation."
        ),
    }


def _summarize_run(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": artifact["artifact_id"],
        "overall_status": artifact["overall_status"],
        "provider": artifact.get("provider"),
        "model": artifact.get("model"),
        "base_url": artifact.get("base_url"),
        "max_segments_per_task": artifact.get("max_segments_per_task"),
        "segment_offset": artifact.get("segment_offset"),
        "prompt_variant": artifact.get("prompt_variant"),
        "accepted_task_count": artifact.get("accepted_task_count", 0),
        "test_improvement_task_count": artifact.get("test_improvement_task_count", 0),
        "task_count": artifact.get("task_count", 0),
        "llm_accounting": artifact.get(
            "llm_accounting",
            {
                "total_call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "parse_failure_count": 0,
            },
        ),
        "task_summaries": {
            task_id: {
                "candidate_accepted": result["candidate_accepted"],
                "accepted_method_id": result["accepted_method_id"],
                "heldout_initial_loss": result["heldout"]["initial_loss"],
                "heldout_final_loss": result["heldout"]["final_loss"],
                "test_initial_loss": result["test"]["initial_loss"],
                "test_final_loss": result["test"]["final_loss"],
                "selected_segments": result["selected_segments"],
            }
            for task_id, result in artifact.get("task_results", {}).items()
        },
    }


def _task_stability(run_results: list[dict[str, Any]]) -> dict[str, Any]:
    task_ids = sorted(
        {
            task_id
            for run in run_results
            for task_id in run.get("task_summaries", {})
        }
    )
    stability = {}
    for task_id in task_ids:
        task_runs = [
            run["task_summaries"][task_id]
            for run in run_results
            if task_id in run.get("task_summaries", {})
        ]
        if not task_runs:
            continue
        accepted_count = sum(1 for run in task_runs if run["candidate_accepted"])
        test_improved_count = sum(
            1 for run in task_runs if run["test_final_loss"] < run["test_initial_loss"]
        )
        stability[task_id] = {
            "run_count": len(task_runs),
            "accepted_count": accepted_count,
            "test_improved_count": test_improved_count,
            "accepted_rate": accepted_count / len(task_runs),
            "test_improved_rate": test_improved_count / len(task_runs),
        }
    return stability


def _planned_matrix(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    segment_scales: list[int],
    segment_offsets: list[int],
    prompt_variants: list[str],
) -> dict[str, Any]:
    matrix = _build_matrix_artifact(
        artifact_id=artifact_id,
        source_artifact_id=microdata_artifact.get("artifact_id"),
        provider=provider,
        model=model,
        base_url=base_url,
        segment_scales=segment_scales,
        segment_offsets=segment_offsets,
        prompt_variants=prompt_variants,
        run_results=[],
    )
    matrix["overall_status"] = "planned_not_executed"
    matrix["risk_flags"] = ["not_executed"]
    return matrix


def _matrix_status(
    *,
    run_count: int,
    positive_run_count: int,
    parse_failure_count: int,
) -> str:
    if run_count == 0:
        return "planned_not_executed"
    if parse_failure_count:
        return "seed_scale_repeat_signal_mixed_parse_risk"
    if positive_run_count == run_count:
        return "seed_scale_repeat_signal_positive"
    if positive_run_count > 0:
        return "seed_scale_repeat_signal_mixed"
    return "seed_scale_repeat_signal_negative"


def _risk_flags(
    *,
    run_count: int,
    positive_run_count: int,
    parse_failure_count: int,
) -> list[str]:
    flags = [
        "not_cross_provider_validation",
        "not_strong_baseline_matrix",
        "not_population_scale_validation",
    ]
    if positive_run_count != run_count:
        flags.append("repeat_instability_observed")
    if parse_failure_count:
        flags.append("llm_parse_failure_observed")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES LLM seed-scale-repeat matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
