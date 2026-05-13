from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EVAL_SIZES = (1, 2, 5)
DATASET_SEEDS = (42,)
PROMPT_BASELINES = ("default",)
TEXTGRAD_TOKEN_BUDGETS = (1024,)
MODES = ("dry-run", "local")
MATRIX_SCHEMA_VERSION = "circe-textgrad-matrix-v1"
MATRIX_CLAIM_BOUNDARY = (
    "bounded TextGrad benchmark matrix plan; not paper-grade TextGrad effectiveness evidence"
)


def build_matrix_plan(
    run_prefix: str = "textgrad-matrix",
    *,
    eval_sizes: tuple[int, ...] = EVAL_SIZES,
    dataset_seeds: tuple[int, ...] = DATASET_SEEDS,
    prompt_baselines: tuple[str, ...] = PROMPT_BASELINES,
    textgrad_token_budgets: tuple[int, ...] = TEXTGRAD_TOKEN_BUDGETS,
    modes: tuple[str, ...] = MODES,
) -> list[dict[str, Any]]:
    plan = []
    use_legacy_run_ids = (
        eval_sizes == EVAL_SIZES
        and dataset_seeds == DATASET_SEEDS
        and prompt_baselines == PROMPT_BASELINES
        and textgrad_token_budgets == TEXTGRAD_TOKEN_BUDGETS
        and modes == MODES
    )
    for mode in modes:
        for seed in dataset_seeds:
            for eval_size in eval_sizes:
                for prompt_baseline in prompt_baselines:
                    for textgrad_budget in textgrad_token_budgets:
                        plan.append(
                            {
                                "run_id": _run_id(
                                    run_prefix=run_prefix,
                                    mode=mode,
                                    dataset_seed=seed,
                                    eval_size=eval_size,
                                    prompt_baseline=prompt_baseline,
                                    textgrad_max_tokens=textgrad_budget,
                                    legacy=use_legacy_run_ids,
                                ),
                                "mode": mode,
                                "dataset_seed": seed,
                                "eval_size": eval_size,
                                "max_iterations": 2,
                                "prompt_baseline": prompt_baseline,
                                "simulator_max_tokens": 256 if mode == "local" else 2000,
                                "textgrad_max_tokens": textgrad_budget,
                                "request_timeout": 90 if mode == "local" else None,
                                "variant": _variant(mode, prompt_baseline, textgrad_budget),
                            }
                        )
    return plan


def summarize_matrix(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    improvement_ratios = [
        float(manifest.get("metrics", {}).get("improvement_ratio", 0.0))
        for manifest in manifests
    ]
    negative_result_count = sum(
        1 for manifest in manifests if _is_negative_textgrad_result(manifest)
    )
    diagnosis_counts: dict[str, int] = {}
    for manifest in manifests:
        for flag in diagnose_manifest(manifest)["flags"]:
            diagnosis_counts[flag] = diagnosis_counts.get(flag, 0) + 1
    return {
        "run_count": len(manifests),
        "best_improvement_ratio": max(improvement_ratios, default=0.0),
        "negative_result_count": negative_result_count,
        "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
    }


def diagnose_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    config = manifest.get("config", {})
    metrics = manifest.get("metrics", {})
    flags: list[str] = []

    eval_size = int(config.get("eval_size", 0) or 0)
    if eval_size <= 1:
        flags.append("eval_size_too_small_to_judge")

    textgrad_calls = int(metrics.get("textgrad_call_count", 0) or 0)
    textgrad_budget = int(config.get("textgrad_max_tokens", 0) or 0)
    output_tokens = int(metrics.get("textgrad_output_tokens", 0) or 0)
    if textgrad_calls > 0 and textgrad_budget > 0:
        if output_tokens >= textgrad_calls * textgrad_budget:
            flags.append("textgrad_output_budget_saturated")

    truncation_count = int(metrics.get("suspected_prompt_truncation_count", 0) or 0)
    if truncation_count > 0:
        flags.append("suspected_prompt_truncation")

    improvement = float(metrics.get("improvement_ratio", 0.0) or 0.0)
    effect_status = metrics.get("textgrad_effect_status")
    if (
        effect_status == "updated_no_improvement"
        and improvement <= 0.0
        and eval_size >= 5
        and "textgrad_output_budget_saturated" not in flags
        and "suspected_prompt_truncation" not in flags
    ):
        flags.append("textgrad_direction_no_measured_gain")

    return {
        "flags": flags,
        "primary_hypothesis": _primary_hypothesis(flags),
    }


def write_matrix_index(
    path: str | Path,
    *,
    matrix_id: str,
    manifest_refs: list[str],
    summary: dict[str, Any] | None = None,
    claim_boundary: str = MATRIX_CLAIM_BOUNDARY,
) -> Path:
    index = {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "matrix_id": matrix_id,
        "manifest_refs": manifest_refs,
        "summary": summary or {},
        "claim_boundary": claim_boundary,
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, allow_nan=False, indent=2, sort_keys=True))
    return output_path


def _is_negative_textgrad_result(manifest: dict[str, Any]) -> bool:
    metrics = manifest.get("metrics", {})
    if metrics.get("textgrad_effect_status") == "updated_no_improvement":
        return True
    return (
        int(metrics.get("textgrad_call_count", 0)) > 0
        and int(metrics.get("prompt_update_count", 0)) > 0
        and float(metrics.get("improvement_ratio", 0.0)) <= 0.0
    )


def _run_id(
    *,
    run_prefix: str,
    mode: str,
    dataset_seed: int,
    eval_size: int,
    prompt_baseline: str,
    textgrad_max_tokens: int,
    legacy: bool = False,
) -> str:
    if legacy and mode == "dry-run":
        return f"{run_prefix}-dry-eval{eval_size}-baseline"
    if legacy and mode == "local":
        return f"{run_prefix}-local-eval{eval_size}-limited"
    normalized_mode = mode.replace("-run", "")
    return (
        f"{run_prefix}-{normalized_mode}-seed{dataset_seed}-eval{eval_size}-"
        f"{prompt_baseline}-tg{textgrad_max_tokens}"
    )


def _variant(mode: str, prompt_baseline: str, textgrad_max_tokens: int) -> str:
    if mode == "dry-run":
        return "baseline"
    if prompt_baseline == "default" and textgrad_max_tokens == 1024:
        return "limited"
    return f"{prompt_baseline}-tg{textgrad_max_tokens}"


def _primary_hypothesis(flags: list[str]) -> str:
    for flag in (
        "textgrad_output_budget_saturated",
        "suspected_prompt_truncation",
        "eval_size_too_small_to_judge",
        "textgrad_direction_no_measured_gain",
    ):
        if flag in flags:
            return flag
    return "no_obvious_matrix_diagnostic"
