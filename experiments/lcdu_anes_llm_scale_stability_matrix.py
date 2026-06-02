from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCALE_STABILITY_SCHEMA_VERSION = "lcdu-anes-llm-scale-stability-matrix-v1"
SEED_SCALE_REPEAT_SCHEMA_VERSION = "lcdu-anes-llm-seed-scale-repeat-matrix-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_llm_scale_stability_matrix(
    *,
    artifact_id: str,
    seed_scale_repeat_matrix: dict[str, Any],
    min_max_segment_scale: int,
    selected_prompt_variant: str,
) -> dict[str, Any]:
    _validate_seed_scale_repeat_matrix(seed_scale_repeat_matrix)
    segment_scales = _segment_scales(seed_scale_repeat_matrix)
    max_segment_scale = max(segment_scales) if segment_scales else 0
    run_count = int(seed_scale_repeat_matrix.get("run_count", 0))
    positive_run_count = int(seed_scale_repeat_matrix.get("positive_run_count", 0))
    task_stability = seed_scale_repeat_matrix.get("task_stability", {})
    artifact = {
        "schema_version": SCALE_STABILITY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            max_segment_scale=max_segment_scale,
            min_max_segment_scale=min_max_segment_scale,
            run_count=run_count,
            positive_run_count=positive_run_count,
            task_stability=task_stability,
            parse_failure_count=seed_scale_repeat_matrix.get("llm_accounting", {}).get(
                "parse_failure_count", 0
            ),
        ),
        "validation_type": "llm_segment_scale_stability_matrix",
        "source_matrix_artifact_id": seed_scale_repeat_matrix["artifact_id"],
        "provider": seed_scale_repeat_matrix.get("provider"),
        "model": seed_scale_repeat_matrix.get("model"),
        "base_url": seed_scale_repeat_matrix.get("base_url"),
        "selected_prompt_variant": selected_prompt_variant,
        "source_prompt_variants": seed_scale_repeat_matrix.get("prompt_variants", []),
        "segment_scales": segment_scales,
        "segment_offsets": seed_scale_repeat_matrix.get("segment_offsets", []),
        "min_max_segment_scale": min_max_segment_scale,
        "max_segment_scale": max_segment_scale,
        "run_count": run_count,
        "positive_run_count": positive_run_count,
        "task_stability": task_stability,
        "llm_accounting": seed_scale_repeat_matrix.get(
            "llm_accounting",
            {
                "total_call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "parse_failure_count": 0,
            },
        ),
        "risk_flags": _risk_flags(
            max_segment_scale=max_segment_scale,
            min_max_segment_scale=min_max_segment_scale,
            run_count=run_count,
            positive_run_count=positive_run_count,
            task_stability=task_stability,
            source_prompt_variants=seed_scale_repeat_matrix.get("prompt_variants", []),
            selected_prompt_variant=selected_prompt_variant,
            parse_failure_count=seed_scale_repeat_matrix.get("llm_accounting", {}).get(
                "parse_failure_count", 0
            ),
        ),
        "claim_boundary": (
            "This artifact checks whether the selected LCDU prompt variant remains "
            "positive when segment coverage expands beyond small smoke settings. "
            "It is still ANES sample-slice evidence, not full population-scale "
            "field validation or strong-baseline superiority."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_llm_scale_stability_matrix(
    output: str | Path,
    *,
    artifact_id: str,
    seed_scale_repeat_matrix_path: str | Path,
    min_max_segment_scale: int,
    selected_prompt_variant: str,
) -> dict[str, Any]:
    artifact = build_lcdu_anes_llm_scale_stability_matrix(
        artifact_id=artifact_id,
        seed_scale_repeat_matrix=load_json_artifact(seed_scale_repeat_matrix_path),
        min_max_segment_scale=min_max_segment_scale,
        selected_prompt_variant=selected_prompt_variant,
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"output_path": str(output_path), "artifact": artifact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed-scale-repeat-matrix",
        required=True,
        help="Seed/scale/repeat matrix artifact to promote into scale stability.",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_llm_scale_stability/"
            "lcdu-anes-llm-scale-stability-matrix-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-llm-scale-stability-matrix-current-001",
    )
    parser.add_argument("--min-max-segment-scale", type=int, default=8)
    parser.add_argument("--selected-prompt-variant", default="deliberative")
    args = parser.parse_args()
    written = write_lcdu_anes_llm_scale_stability_matrix(
        args.output,
        artifact_id=args.artifact_id,
        seed_scale_repeat_matrix_path=args.seed_scale_repeat_matrix,
        min_max_segment_scale=args.min_max_segment_scale,
        selected_prompt_variant=args.selected_prompt_variant,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "max_segment_scale": artifact["max_segment_scale"],
                "output": written["output_path"],
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
        raise ValueError("seed_scale_repeat_matrix must include runs")


def _segment_scales(matrix: dict[str, Any]) -> list[int]:
    declared = matrix.get("segment_scales")
    if isinstance(declared, list) and declared:
        return sorted({int(scale) for scale in declared})
    run_results = matrix.get("run_results")
    if isinstance(run_results, list):
        return sorted(
            {
                int(run["max_segments_per_task"])
                for run in run_results
                if "max_segments_per_task" in run
            }
        )
    return []


def _overall_status(
    *,
    max_segment_scale: int,
    min_max_segment_scale: int,
    run_count: int,
    positive_run_count: int,
    task_stability: dict[str, Any],
    parse_failure_count: int,
) -> str:
    if max_segment_scale < min_max_segment_scale:
        return "scale_stability_evidence_insufficient"
    if parse_failure_count:
        return "scale_stability_signal_mixed_parse_risk"
    if positive_run_count == run_count and _all_tasks_stable(task_stability):
        return "scale_stability_signal_positive"
    if positive_run_count > 0:
        return "scale_stability_signal_mixed"
    return "scale_stability_signal_negative"


def _all_tasks_stable(task_stability: dict[str, Any]) -> bool:
    if not isinstance(task_stability, dict) or not task_stability:
        return False
    return all(
        stability.get("accepted_rate") == 1.0
        and stability.get("test_improved_rate") == 1.0
        for stability in task_stability.values()
    )


def _risk_flags(
    *,
    max_segment_scale: int,
    min_max_segment_scale: int,
    run_count: int,
    positive_run_count: int,
    task_stability: dict[str, Any],
    source_prompt_variants: list[str],
    selected_prompt_variant: str,
    parse_failure_count: int,
) -> list[str]:
    flags = [
        "not_full_population_field_validation",
        "not_strong_baseline_matrix",
        "single_provider_scale_evidence",
    ]
    if max_segment_scale < min_max_segment_scale:
        flags.append("scale_evidence_insufficient")
    if positive_run_count != run_count or not _all_tasks_stable(task_stability):
        flags.append("scale_instability_observed")
    if parse_failure_count:
        flags.append("llm_parse_failure_observed")
    if source_prompt_variants != [selected_prompt_variant]:
        flags.append("scale_matrix_not_single_selected_variant")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES LLM scale stability matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
