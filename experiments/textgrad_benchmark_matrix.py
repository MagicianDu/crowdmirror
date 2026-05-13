from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EVAL_SIZES = (1, 2, 5)
DATASET_SEEDS = (42,)
PROMPT_BASELINES = ("default",)
TEXTGRAD_TOKEN_BUDGETS = (1024,)
MODES = ("dry-run", "local")
PAPER_GATE_EVAL_SIZE = 5
PAPER_GATE_SEEDS = (42, 7, 99)
PAPER_GATE_PROMPT_BASELINES = ("default", "compact", "structured")
PAPER_GATE_TEXTGRAD_TOKEN_BUDGETS = (1024, 2048)
PAPER_GATE_REPEATS = 3
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
        **_candidate_acceptance_totals(manifests),
    }


def build_paper_gate_plan(
    run_prefix: str = "textgrad-paper-gate",
    *,
    dataset_seeds: tuple[int, ...] = PAPER_GATE_SEEDS,
    prompt_baselines: tuple[str, ...] = PAPER_GATE_PROMPT_BASELINES,
    textgrad_token_budgets: tuple[int, ...] = PAPER_GATE_TEXTGRAD_TOKEN_BUDGETS,
    repeats: int = PAPER_GATE_REPEATS,
    eval_size: int = PAPER_GATE_EVAL_SIZE,
) -> list[dict[str, Any]]:
    if eval_size < PAPER_GATE_EVAL_SIZE:
        raise ValueError("paper gate eval_size must be at least 5")
    if repeats <= 0:
        raise ValueError("repeats must be positive")

    plan = []
    for seed in dataset_seeds:
        for prompt_baseline in prompt_baselines:
            for textgrad_budget in textgrad_token_budgets:
                for repeat in range(1, repeats + 1):
                    plan.append(
                        {
                            "run_id": (
                                f"{run_prefix}-local-seed{seed}-eval{eval_size}-"
                                f"{prompt_baseline}-tg{textgrad_budget}-r{repeat}"
                            ),
                            "mode": "local",
                            "dataset_seed": seed,
                            "eval_size": eval_size,
                            "max_iterations": 2,
                            "prompt_baseline": prompt_baseline,
                            "simulator_max_tokens": 256,
                            "textgrad_max_tokens": textgrad_budget,
                            "request_timeout": 240,
                            "repeat": repeat,
                            "variant": f"{prompt_baseline}-tg{textgrad_budget}",
                        }
                    )
    return plan


def evaluate_paper_gate(
    manifests: list[dict[str, Any]],
    *,
    required_seeds: tuple[int, ...] = PAPER_GATE_SEEDS,
    required_prompt_baselines: tuple[str, ...] = PAPER_GATE_PROMPT_BASELINES,
    required_textgrad_token_budgets: tuple[int, ...] = PAPER_GATE_TEXTGRAD_TOKEN_BUDGETS,
    required_repeats: int = PAPER_GATE_REPEATS,
    min_eval_size: int = PAPER_GATE_EVAL_SIZE,
) -> dict[str, Any]:
    required_cells = _required_cells(
        required_seeds=required_seeds,
        required_prompt_baselines=required_prompt_baselines,
        required_textgrad_token_budgets=required_textgrad_token_budgets,
        required_repeats=required_repeats,
    )
    observed_cells = {
        _manifest_cell(manifest)
        for manifest in manifests
        if int(manifest.get("config", {}).get("eval_size", 0) or 0) >= min_eval_size
    }
    observed_seeds = {cell[0] for cell in observed_cells}
    missing_cells = sorted(required_cells - observed_cells)
    improved_run_count = sum(
        1 for manifest in manifests
        if manifest.get("metrics", {}).get("textgrad_effect_status") == "improved"
    )
    negative_result_count = sum(
        1 for manifest in manifests if _is_negative_textgrad_result(manifest)
    )
    candidate_acceptance = _candidate_acceptance_totals(manifests)

    if missing_cells:
        status = "insufficient_evidence"
    elif negative_result_count > 0:
        status = "failed"
    else:
        status = "passed"

    return {
        "status": status,
        "observed_run_count": len(observed_cells),
        "required_run_count": len(required_cells),
        "missing_cells": _missing_cell_labels(
            missing_cells,
            required_seeds,
            observed_seeds,
        ),
        "improved_run_count": improved_run_count,
        "negative_result_count": negative_result_count,
        **candidate_acceptance,
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

    if int(metrics.get("candidate_rejected_count", 0) or 0) > 0:
        flags.append("candidate_update_rejected")

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


def _candidate_acceptance_totals(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    update_count = 0
    evaluated_count = 0
    accepted_count = 0
    rejected_count = 0
    pending_count = 0
    for manifest in manifests:
        metrics = manifest.get("metrics", {})
        update_count += int(metrics.get("candidate_update_count", 0) or 0)
        evaluated_count += int(metrics.get("candidate_evaluated_count", 0) or 0)
        accepted_count += int(metrics.get("candidate_accepted_count", 0) or 0)
        rejected_count += int(metrics.get("candidate_rejected_count", 0) or 0)
        pending_count += int(metrics.get("candidate_pending_count", 0) or 0)
    acceptance_rate = (
        accepted_count / evaluated_count if evaluated_count > 0 else None
    )
    return {
        "candidate_update_count": update_count,
        "candidate_evaluated_count": evaluated_count,
        "candidate_accepted_count": accepted_count,
        "candidate_rejected_count": rejected_count,
        "candidate_pending_count": pending_count,
        "candidate_acceptance_rate": acceptance_rate,
    }


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


def _required_cells(
    *,
    required_seeds: tuple[int, ...],
    required_prompt_baselines: tuple[str, ...],
    required_textgrad_token_budgets: tuple[int, ...],
    required_repeats: int,
) -> set[tuple[int, str, int, int]]:
    return {
        (seed, prompt_baseline, budget, repeat)
        for seed in required_seeds
        for prompt_baseline in required_prompt_baselines
        for budget in required_textgrad_token_budgets
        for repeat in range(1, required_repeats + 1)
    }


def _manifest_cell(manifest: dict[str, Any]) -> tuple[int, str, int, int]:
    config = manifest.get("config", {})
    return (
        int(config.get("dataset_seed")),
        str(config.get("prompt_baseline")),
        int(config.get("textgrad_max_tokens")),
        _manifest_repeat(manifest),
    )


def _manifest_repeat(manifest: dict[str, Any]) -> int:
    config = manifest.get("config", {})
    if "repeat" in config:
        return int(config.get("repeat") or 1)
    run_id = str(manifest.get("run_id", ""))
    repeat_token = run_id.rsplit("-r", 1)
    if len(repeat_token) == 2 and repeat_token[1].isdigit():
        return int(repeat_token[1])
    return 1


def _missing_cell_labels(
    missing_cells: list[tuple[int, str, int, int]],
    required_seeds: tuple[int, ...],
    observed_seeds: set[int],
) -> list[str]:
    labels: list[str] = []
    missing_seeds = {
        seed
        for seed in required_seeds
        if seed not in observed_seeds
    }
    for seed in sorted(missing_seeds):
        labels.append(f"missing_seed:{seed}")
    labels.extend(
        f"missing_cell:seed{seed}:{baseline}:tg{budget}:r{repeat}"
        for seed, baseline, budget, repeat in missing_cells
    )
    return labels
