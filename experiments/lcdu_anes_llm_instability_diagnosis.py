from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.lcdu_anes_llm_simulator_validation import (  # noqa: E402
    _build_completion_fn,
    build_lcdu_anes_llm_simulator_validation_artifact,
    load_json_artifact,
)


DIAGNOSIS_SCHEMA_VERSION = "lcdu-anes-llm-instability-diagnosis-v1"
MATRIX_SCHEMA_VERSION = "lcdu-anes-llm-seed-scale-repeat-matrix-v1"
LLM_VALIDATION_SCHEMA_VERSION = "lcdu-anes-llm-simulator-validation-v1"


def build_lcdu_anes_llm_instability_diagnosis(
    *,
    artifact_id: str,
    seed_scale_repeat_matrix: dict[str, Any],
    diagnosis_run_artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    _validate_seed_scale_repeat_matrix(seed_scale_repeat_matrix)
    validated_runs = diagnosis_run_artifacts or []
    for run_artifact in validated_runs:
        _validate_diagnosis_run(run_artifact)

    failure_cases = _failure_cases(seed_scale_repeat_matrix)
    diagnosis_runs = [_summarize_diagnosis_run(run) for run in validated_runs]
    recovery_cases = [
        recovery
        for failure_case in failure_cases
        if (recovery := _matching_recovery(failure_case, diagnosis_runs)) is not None
    ]
    recovered_case_keys = {
        _case_key(recovery["source_failure_case"]) for recovery in recovery_cases
    }
    persistent_failure_cases = [
        failure_case
        for failure_case in failure_cases
        if _case_key(failure_case) not in recovered_case_keys
    ]

    artifact = {
        "schema_version": DIAGNOSIS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            failure_count=len(failure_cases),
            diagnosis_run_count=len(diagnosis_runs),
            recovered_failure_count=len(recovery_cases),
        ),
        "source_matrix_artifact_id": seed_scale_repeat_matrix["artifact_id"],
        "provider": seed_scale_repeat_matrix.get("provider"),
        "model": seed_scale_repeat_matrix.get("model"),
        "base_url": seed_scale_repeat_matrix.get("base_url"),
        "diagnosis_type": "targeted_prompt_variant_recovery_probe",
        "failure_count": len(failure_cases),
        "recovered_failure_count": len(recovery_cases),
        "persistent_failure_count": len(persistent_failure_cases),
        "failure_cases": failure_cases,
        "diagnosis_runs": diagnosis_runs,
        "recovery_cases": recovery_cases,
        "persistent_failure_cases": persistent_failure_cases,
        "llm_accounting": _llm_accounting(diagnosis_runs),
        "hypotheses": _hypotheses(
            failure_cases=failure_cases,
            recovery_cases=recovery_cases,
            persistent_failure_cases=persistent_failure_cases,
        ),
        "risk_flags": _risk_flags(
            failure_count=len(failure_cases),
            diagnosis_run_count=len(diagnosis_runs),
            recovered_failure_count=len(recovery_cases),
            persistent_failure_count=len(persistent_failure_cases),
        ),
        "claim_boundary": (
            "This diagnosis identifies whether a mixed seed/scale/repeat signal "
            "is recoverable by targeted prompt variants for the same segment "
            "selection. It is not a full prompt-variant matrix, cross-provider "
            "proof, strong-baseline comparison, or population-scale validation."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_llm_instability_diagnosis(
    output: str | Path,
    *,
    seed_scale_repeat_matrix_path: str | Path,
    artifact_id: str,
    microdata_artifact_path: str | Path | None,
    provider: str,
    model: str,
    base_url: str | None,
    prompt_variants: list[str],
    execute: bool,
) -> dict[str, Any]:
    matrix = load_json_artifact(seed_scale_repeat_matrix_path)
    diagnosis_run_artifacts = []
    if execute:
        if microdata_artifact_path is None:
            raise ValueError("microdata_artifact_path is required when execute=True")
        microdata_artifact = load_json_artifact(microdata_artifact_path)
        completion_fn = _build_completion_fn(
            provider=provider,
            model=model,
            base_url=base_url,
        )
        for config in _targeted_run_configs(matrix):
            for prompt_variant in prompt_variants:
                run_id = (
                    f"{artifact_id}-scale{config['max_segments_per_task']}-"
                    f"offset{config['segment_offset']}-{prompt_variant}"
                )
                diagnosis_run_artifacts.append(
                    build_lcdu_anes_llm_simulator_validation_artifact(
                        microdata_artifact=microdata_artifact,
                        artifact_id=run_id,
                        provider=provider,
                        model=model,
                        base_url=base_url,
                        completion_fn=completion_fn,
                        max_segments_per_task=config["max_segments_per_task"],
                        segment_offset=config["segment_offset"],
                        prompt_variant=prompt_variant,
                    )
                )
    diagnosis = build_lcdu_anes_llm_instability_diagnosis(
        artifact_id=artifact_id,
        seed_scale_repeat_matrix=matrix,
        diagnosis_run_artifacts=diagnosis_run_artifacts,
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(diagnosis, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"output_path": str(output_path), "artifact": diagnosis}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed-scale-repeat-matrix",
        default=(
            "experiments/results/lcdu_llm_seed_scale_repeat/"
            "lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-standard-001.json"
        ),
    )
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
            "experiments/results/lcdu_llm_instability_diagnosis/"
            "lcdu-anes-llm-instability-diagnosis-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-llm-instability-diagnosis-current-001",
    )
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument(
        "--prompt-variants",
        nargs="+",
        choices=["standard", "compact", "deliberative"],
        default=["compact", "deliberative"],
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    written = write_lcdu_anes_llm_instability_diagnosis(
        args.output,
        seed_scale_repeat_matrix_path=args.seed_scale_repeat_matrix,
        artifact_id=args.artifact_id,
        microdata_artifact_path=args.microdata_artifact,
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        prompt_variants=args.prompt_variants,
        execute=args.execute,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "failure_count": artifact["failure_count"],
                "output": written["output_path"],
                "recovered_failure_count": artifact["recovered_failure_count"],
                "status": artifact["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_seed_scale_repeat_matrix(matrix: dict[str, Any]) -> None:
    if matrix.get("schema_version") != MATRIX_SCHEMA_VERSION:
        raise ValueError("seed_scale_repeat_matrix has unsupported schema_version")
    if matrix.get("validation_type") != "llm_seed_scale_repeat_matrix":
        raise ValueError("seed_scale_repeat_matrix has unsupported validation_type")
    if not isinstance(matrix.get("run_results"), list):
        raise ValueError("seed_scale_repeat_matrix missing run_results")


def _validate_diagnosis_run(run_artifact: dict[str, Any]) -> None:
    if run_artifact.get("schema_version") != LLM_VALIDATION_SCHEMA_VERSION:
        raise ValueError("diagnosis run has unsupported schema_version")
    if run_artifact.get("validation_type") != "split_gated_llm_segment_simulator_smoke":
        raise ValueError("diagnosis run has unsupported validation_type")
    if not isinstance(run_artifact.get("task_results"), dict):
        raise ValueError("diagnosis run missing task_results")


def _failure_cases(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    for run in matrix["run_results"]:
        for task_id, task_summary in run.get("task_summaries", {}).items():
            if _task_summary_is_failure(task_summary):
                cases.append(_failure_case(run, task_id, task_summary))
    return cases


def _task_summary_is_failure(task_summary: dict[str, Any]) -> bool:
    return (
        not task_summary.get("candidate_accepted")
        or task_summary.get("test_final_loss", 0.0)
        >= task_summary.get("test_initial_loss", 0.0)
    )


def _failure_case(
    run: dict[str, Any],
    task_id: str,
    task_summary: dict[str, Any],
) -> dict[str, Any]:
    accepted = bool(task_summary.get("candidate_accepted"))
    test_improved = task_summary.get("test_final_loss", 0.0) < task_summary.get(
        "test_initial_loss", 0.0
    )
    if not accepted and not test_improved:
        failure_type = "candidate_rejected_and_test_not_improved"
    elif not accepted:
        failure_type = "candidate_rejected_despite_test_improvement"
    else:
        failure_type = "candidate_accepted_but_test_not_improved"
    return {
        "source_run_id": run["artifact_id"],
        "task_id": task_id,
        "failure_type": failure_type,
        "max_segments_per_task": run.get("max_segments_per_task"),
        "segment_offset": run.get("segment_offset"),
        "prompt_variant": run.get("prompt_variant"),
        "accepted_method_id": task_summary.get("accepted_method_id"),
        "heldout_initial_loss": task_summary.get("heldout_initial_loss"),
        "heldout_final_loss": task_summary.get("heldout_final_loss"),
        "test_initial_loss": task_summary.get("test_initial_loss"),
        "test_final_loss": task_summary.get("test_final_loss"),
        "selected_segments": task_summary.get("selected_segments", []),
    }


def _summarize_diagnosis_run(run_artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": run_artifact["artifact_id"],
        "overall_status": run_artifact["overall_status"],
        "provider": run_artifact.get("provider"),
        "model": run_artifact.get("model"),
        "base_url": run_artifact.get("base_url"),
        "max_segments_per_task": run_artifact.get("max_segments_per_task"),
        "segment_offset": run_artifact.get("segment_offset"),
        "prompt_variant": run_artifact.get("prompt_variant"),
        "task_summaries": {
            task_id: {
                "candidate_accepted": task_result["candidate_accepted"],
                "accepted_method_id": task_result["accepted_method_id"],
                "heldout_initial_loss": task_result["heldout"]["initial_loss"],
                "heldout_final_loss": task_result["heldout"]["final_loss"],
                "test_initial_loss": task_result["test"]["initial_loss"],
                "test_final_loss": task_result["test"]["final_loss"],
                "selected_segments": task_result["selected_segments"],
            }
            for task_id, task_result in run_artifact.get("task_results", {}).items()
        },
        "llm_accounting": run_artifact.get(
            "llm_accounting",
            {
                "total_call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "parse_failure_count": 0,
            },
        ),
    }


def _matching_recovery(
    failure_case: dict[str, Any],
    diagnosis_runs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for run in diagnosis_runs:
        if run.get("max_segments_per_task") != failure_case.get("max_segments_per_task"):
            continue
        if run.get("segment_offset") != failure_case.get("segment_offset"):
            continue
        task_summary = run["task_summaries"].get(failure_case["task_id"])
        if task_summary is None:
            continue
        if task_summary.get("selected_segments") != failure_case.get(
            "selected_segments"
        ):
            continue
        if not task_summary.get("candidate_accepted"):
            continue
        if task_summary.get("test_final_loss", 0.0) >= task_summary.get(
            "test_initial_loss", 0.0
        ):
            continue
        return {
            "source_failure_case": failure_case,
            "diagnosis_run_id": run["artifact_id"],
            "task_id": failure_case["task_id"],
            "recovered_by_prompt_variant": run["prompt_variant"],
            "accepted_method_id": task_summary.get("accepted_method_id"),
            "heldout_initial_loss": task_summary.get("heldout_initial_loss"),
            "heldout_final_loss": task_summary.get("heldout_final_loss"),
            "test_initial_loss": task_summary.get("test_initial_loss"),
            "test_final_loss": task_summary.get("test_final_loss"),
        }
    return None


def _targeted_run_configs(matrix: dict[str, Any]) -> list[dict[str, int]]:
    configs = []
    seen = set()
    for failure_case in _failure_cases(matrix):
        key = (
            failure_case["max_segments_per_task"],
            failure_case["segment_offset"],
        )
        if key in seen:
            continue
        seen.add(key)
        configs.append(
            {
                "max_segments_per_task": failure_case["max_segments_per_task"],
                "segment_offset": failure_case["segment_offset"],
            }
        )
    return configs


def _overall_status(
    *,
    failure_count: int,
    diagnosis_run_count: int,
    recovered_failure_count: int,
) -> str:
    if failure_count == 0:
        return "no_instability_detected"
    if diagnosis_run_count == 0:
        return "instability_needs_targeted_diagnosis"
    if recovered_failure_count == failure_count:
        return "instability_recovered_by_prompt_variant"
    if recovered_failure_count > 0:
        return "instability_partially_recovered_by_prompt_variant"
    return "instability_persistent_after_prompt_variants"


def _case_key(case: dict[str, Any]) -> tuple[Any, ...]:
    return (
        case.get("source_run_id"),
        case.get("task_id"),
        case.get("max_segments_per_task"),
        case.get("segment_offset"),
        tuple(case.get("selected_segments", [])),
    )


def _llm_accounting(diagnosis_runs: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_call_count": sum(
            run["llm_accounting"]["total_call_count"] for run in diagnosis_runs
        ),
        "total_input_tokens": sum(
            run["llm_accounting"]["total_input_tokens"] for run in diagnosis_runs
        ),
        "total_output_tokens": sum(
            run["llm_accounting"]["total_output_tokens"] for run in diagnosis_runs
        ),
        "parse_failure_count": sum(
            run["llm_accounting"]["parse_failure_count"] for run in diagnosis_runs
        ),
    }


def _hypotheses(
    *,
    failure_cases: list[dict[str, Any]],
    recovery_cases: list[dict[str, Any]],
    persistent_failure_cases: list[dict[str, Any]],
) -> list[dict[str, str]]:
    hypotheses = []
    if failure_cases:
        hypotheses.append(
            {
                "hypothesis_id": "h1_segment_local_instability",
                "status": "supported",
                "summary": (
                    "Instability is localized to specific task/segment/run "
                    "combinations rather than the full cross-task matrix."
                ),
            }
        )
    if recovery_cases:
        hypotheses.append(
            {
                "hypothesis_id": "h2_prompt_variant_sensitivity",
                "status": "supported",
                "summary": (
                    "At least one failed case is recoverable by changing the "
                    "prompt variant while keeping scale and segment offset fixed."
                ),
            }
        )
    if persistent_failure_cases:
        hypotheses.append(
            {
                "hypothesis_id": "h3_anchor_mechanism_boundary",
                "status": "open",
                "summary": (
                    "Some failures persist after prompt-variant probing and need "
                    "guarded update, stronger baseline, or failure-boundary analysis."
                ),
            }
        )
    if not hypotheses:
        hypotheses.append(
            {
                "hypothesis_id": "h0_no_instability",
                "status": "supported",
                "summary": "No task-level instability was detected in the source matrix.",
            }
        )
    return hypotheses


def _risk_flags(
    *,
    failure_count: int,
    diagnosis_run_count: int,
    recovered_failure_count: int,
    persistent_failure_count: int,
) -> list[str]:
    flags = [
        "not_cross_provider_validation",
        "not_strong_baseline_matrix",
        "not_population_scale_validation",
    ]
    if failure_count:
        flags.append("seed_scale_repeat_instability_observed")
    if diagnosis_run_count:
        flags.append("targeted_diagnosis_not_full_matrix")
    if recovered_failure_count:
        flags.append("prompt_variant_sensitivity_observed")
    if persistent_failure_count:
        flags.append("persistent_failure_boundary_observed")
    if failure_count and not diagnosis_run_count:
        flags.append("targeted_diagnosis_pending")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES LLM instability diagnosis must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
