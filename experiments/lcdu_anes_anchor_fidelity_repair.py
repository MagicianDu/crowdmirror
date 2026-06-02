from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from circe.llm_client import LLMClient, LLMClientConfig, LLMResponse  # noqa: E402
from experiments.lcdu_anes_cross_task_validation import (  # noqa: E402
    _weighted_segment_jsd,
    _worst_segment_jsd,
)
from experiments.lcdu_anes_llm_simulator_validation import (  # noqa: E402
    _parse_distribution,
)


ANCHOR_REPAIR_SCHEMA_VERSION = "lcdu-anes-anchor-fidelity-repair-v1"
MICRODATA_SCHEMA_VERSION = "lcdu-anes-public-microdata-ingestion-v1"
STRONG_BASELINE_SCHEMA_VERSION = "lcdu-anes-strong-baseline-matrix-v1"
CompletionFn = Callable[[str, str], LLMResponse]


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_anchor_fidelity_repair_artifact(
    *,
    microdata_artifact: dict[str, Any],
    strong_baseline_matrix: dict[str, Any],
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    completion_fn: CompletionFn | None = None,
    execute_llm_copy: bool = False,
    max_segments_per_task: int | None = None,
) -> dict[str, Any]:
    _validate_microdata_artifact(microdata_artifact)
    _validate_strong_baseline_matrix(strong_baseline_matrix)
    task_results = {}
    call_records = []
    for task_id in sorted(microdata_artifact["target_distributions"]):
        task_result, task_calls = _evaluate_task(
            task_id=task_id,
            splits=microdata_artifact["splits"],
            strong_baseline_matrix=strong_baseline_matrix,
            completion_fn=completion_fn,
            execute_llm_copy=execute_llm_copy,
            max_segments_per_task=max_segments_per_task,
        )
        task_results[task_id] = task_result
        call_records.extend(task_calls)
    deterministic_closes_count = sum(
        1
        for result in task_results.values()
        if result["deterministic_anchor_copy"]["closes_lcdu_gap"]
    )
    llm_copy_results = [
        result.get("llm_anchor_copy")
        for result in task_results.values()
        if result.get("llm_anchor_copy") is not None
    ]
    llm_copy_closes_count = sum(
        1 for result in llm_copy_results if result["closes_lcdu_gap"]
    )
    artifact = {
        "schema_version": ANCHOR_REPAIR_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            task_count=len(task_results),
            deterministic_closes_count=deterministic_closes_count,
            llm_copy_results=llm_copy_results,
            llm_copy_closes_count=llm_copy_closes_count,
        ),
        "validation_type": "lcdu_anchor_fidelity_repair_diagnostic",
        "source_artifact_ids": [
            microdata_artifact["artifact_id"],
            strong_baseline_matrix["artifact_id"],
        ],
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "execute_llm_copy": execute_llm_copy,
        "max_segments_per_task": max_segments_per_task,
        "candidate_generation_split": "calibration",
        "candidate_acceptance_split": "heldout",
        "final_claim_check_split": "test",
        "task_count": len(task_results),
        "deterministic_closes_count": deterministic_closes_count,
        "llm_copy_closes_count": llm_copy_closes_count,
        "task_results": task_results,
        "llm_accounting": {
            "total_call_count": len(call_records),
            "total_input_tokens": sum(call["input_tokens"] for call in call_records),
            "total_output_tokens": sum(call["output_tokens"] for call in call_records),
            "parse_failure_count": sum(
                1 for call in call_records if not call["parse_success"]
            ),
        },
        "call_records": call_records,
        "risk_flags": _risk_flags(
            execute_llm_copy=execute_llm_copy,
            llm_copy_results=llm_copy_results,
        ),
        "claim_boundary": (
            "This artifact diagnoses whether the LCDU anchor-fidelity gap can be "
            "closed by separating numeric segment anchors from LLM narrative or "
            "by asking an LLM to strictly copy calibration anchors. It is a "
            "repair diagnostic, not evidence that the original LCDU LLM prompt "
            "already beats strong baselines."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_anchor_fidelity_repair_artifact(
    output: str | Path,
    *,
    microdata_artifact_path: str | Path,
    strong_baseline_matrix_path: str | Path,
    artifact_id: str,
    provider: str,
    model: str,
    base_url: str | None,
    execute_llm_copy: bool,
    max_segments_per_task: int | None,
    timeout_seconds: float | None,
) -> dict[str, Any]:
    completion_fn = None
    if execute_llm_copy:
        completion_fn = _build_completion_fn(
            provider=provider,
            model=model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )
    artifact = build_lcdu_anes_anchor_fidelity_repair_artifact(
        microdata_artifact=load_json_artifact(microdata_artifact_path),
        strong_baseline_matrix=load_json_artifact(strong_baseline_matrix_path),
        artifact_id=artifact_id,
        provider=provider,
        model=model,
        base_url=base_url,
        completion_fn=completion_fn,
        execute_llm_copy=execute_llm_copy,
        max_segments_per_task=max_segments_per_task,
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"artifact": artifact, "output_path": str(output_path)}


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
        "--strong-baseline-matrix",
        default=(
            "experiments/results/lcdu_strong_baseline/"
            "lcdu-anes-strong-baseline-matrix-anes-current-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_anchor_fidelity_repair/"
            "lcdu-anes-anchor-fidelity-repair-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-anchor-fidelity-repair-current-001",
    )
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--execute-llm-copy", action="store_true")
    parser.add_argument("--max-segments-per-task", type=int, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args()
    written = write_lcdu_anes_anchor_fidelity_repair_artifact(
        args.output,
        microdata_artifact_path=args.microdata_artifact,
        strong_baseline_matrix_path=args.strong_baseline_matrix,
        artifact_id=args.artifact_id,
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        execute_llm_copy=args.execute_llm_copy,
        max_segments_per_task=args.max_segments_per_task,
        timeout_seconds=args.timeout_seconds,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "deterministic_closes_count": artifact["deterministic_closes_count"],
                "llm_copy_closes_count": artifact["llm_copy_closes_count"],
                "output": written["output_path"],
                "status": artifact["overall_status"],
                "task_count": artifact["task_count"],
                "total_call_count": artifact["llm_accounting"]["total_call_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_microdata_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != MICRODATA_SCHEMA_VERSION:
        raise ValueError("microdata artifact has unsupported schema_version")
    if "splits" not in artifact or "target_distributions" not in artifact:
        raise ValueError("microdata artifact missing splits or targets")
    if set(artifact["splits"]) != {"calibration", "heldout", "test"}:
        raise ValueError("microdata artifact must include calibration/heldout/test")


def _validate_strong_baseline_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != STRONG_BASELINE_SCHEMA_VERSION:
        raise ValueError("strong baseline matrix has unsupported schema_version")
    if not isinstance(artifact.get("task_results"), dict):
        raise ValueError("strong baseline matrix missing task_results")


def _evaluate_task(
    *,
    task_id: str,
    splits: dict[str, Any],
    strong_baseline_matrix: dict[str, Any],
    completion_fn: CompletionFn | None,
    execute_llm_copy: bool,
    max_segments_per_task: int | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    calibration = splits["calibration"]["target_distributions"][task_id]
    heldout = splits["heldout"]["target_distributions"][task_id]
    test = splits["test"]["target_distributions"][task_id]
    strong_task = strong_baseline_matrix["task_results"][task_id]
    selected_segments = _select_segments(
        calibration=calibration,
        heldout=heldout,
        test=test,
        max_segments=max_segments_per_task,
    )
    deterministic_predictions = {
        segment_key: calibration["by_segment"][segment_key]["policy_probabilities"]
        for segment_key in selected_segments
    }
    heldout_selected = _filter_segments(heldout["by_segment"], selected_segments)
    test_selected = _filter_segments(test["by_segment"], selected_segments)
    deterministic = _score_prediction(
        observed_heldout=heldout_selected,
        observed_test=test_selected,
        prediction=deterministic_predictions,
        current_lcdu_test_loss=strong_task["lcdU_test_loss"],
    )
    result = {
        "task_id": task_id,
        "selected_segments": selected_segments,
        "current_lcdu": {
            "test_loss": strong_task["lcdU_test_loss"],
            "selected_source_artifact_id": strong_task.get(
                "lcdU_selected_source_artifact_id"
            ),
            "selected_heldout_loss": strong_task.get("lcdU_selected_heldout_loss"),
        },
        "best_covered_baseline": {
            "baseline_family": strong_task["best_covered_baseline_family"],
            "method_id": strong_task["best_covered_baseline_method_id"],
            "test_loss": strong_task["best_covered_baseline_test_loss"],
        },
        "deterministic_anchor_copy": deterministic,
        "interpretation": (
            "numeric_anchor_hybrid_closes_gap"
            if deterministic["closes_lcdu_gap"]
            else "numeric_anchor_hybrid_does_not_close_gap"
        ),
    }
    call_records = []
    if execute_llm_copy:
        if completion_fn is None:
            raise ValueError("completion_fn is required when execute_llm_copy is true")
        llm_prediction, call_records = _run_llm_anchor_copy(
            task_id=task_id,
            calibration=calibration,
            selected_segments=selected_segments,
            completion_fn=completion_fn,
        )
        llm_score = _score_prediction(
            observed_heldout=heldout_selected,
            observed_test=test_selected,
            prediction=llm_prediction,
            current_lcdu_test_loss=strong_task["lcdU_test_loss"],
        )
        llm_score["mean_anchor_l1_deviation"] = _mean_anchor_l1_deviation(
            deterministic_predictions,
            llm_prediction,
        )
        llm_score["max_anchor_l1_deviation"] = _max_anchor_l1_deviation(
            deterministic_predictions,
            llm_prediction,
        )
        result["llm_anchor_copy"] = llm_score
        if llm_score["closes_lcdu_gap"]:
            result["interpretation"] = "llm_anchor_copy_closes_gap"
    return result, call_records


def _select_segments(
    *,
    calibration: dict[str, Any],
    heldout: dict[str, Any],
    test: dict[str, Any],
    max_segments: int | None,
) -> list[str]:
    common_segments = sorted(
        set(calibration["by_segment"])
        & set(heldout["by_segment"])
        & set(test["by_segment"]),
        key=lambda segment_key: heldout["by_segment"][segment_key]["row_count"],
        reverse=True,
    )
    if max_segments is None:
        return common_segments
    return common_segments[:max_segments]


def _filter_segments(
    by_segment: dict[str, Any],
    selected_segments: list[str],
) -> dict[str, Any]:
    return {
        segment_key: by_segment[segment_key]
        for segment_key in selected_segments
        if segment_key in by_segment
    }


def _score_prediction(
    *,
    observed_heldout: dict[str, Any],
    observed_test: dict[str, Any],
    prediction: dict[str, dict[str, float]],
    current_lcdu_test_loss: float,
) -> dict[str, Any]:
    heldout_loss = _weighted_segment_jsd(
        observed_by_segment=observed_heldout,
        predicted_by_segment=prediction,
    )
    test_loss = _weighted_segment_jsd(
        observed_by_segment=observed_test,
        predicted_by_segment=prediction,
    )
    return {
        "heldout_loss": heldout_loss,
        "test_loss": test_loss,
        "test_worst_segment_loss": _worst_segment_jsd(
            observed_by_segment=observed_test,
            predicted_by_segment=prediction,
        ),
        "loss_delta_vs_current_lcdu": test_loss - current_lcdu_test_loss,
        "closes_lcdu_gap": test_loss <= current_lcdu_test_loss,
    }


def _run_llm_anchor_copy(
    *,
    task_id: str,
    calibration: dict[str, Any],
    selected_segments: list[str],
    completion_fn: CompletionFn,
) -> tuple[dict[str, dict[str, float]], list[dict[str, Any]]]:
    predictions = {}
    call_records = []
    policy_options = list(calibration["overall"]["policy_probabilities"])
    for segment_key in selected_segments:
        anchor = calibration["by_segment"][segment_key]["policy_probabilities"]
        system = (
            "Return strict JSON only. Copy the provided anchor probabilities "
            "exactly. Do not infer, smooth, round, or rename keys."
        )
        user = (
            f"Task: {task_id}\n"
            f"Segment key: {segment_key}\n"
            f"Policy keys: {json.dumps(policy_options)}\n"
            f"Anchor JSON: {json.dumps(anchor, sort_keys=True)}\n"
            "Return the Anchor JSON exactly."
        )
        response = completion_fn(system, user)
        parsed = _parse_distribution(response.content, policy_options)
        predictions[segment_key] = parsed["probabilities"]
        call_records.append(
            {
                "task_id": task_id,
                "segment_key": segment_key,
                "parse_success": parsed["parse_success"],
                "parsed_policy_probabilities": parsed["probabilities"],
                "anchor_policy_probabilities": anchor,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "anchor_l1_deviation": _l1(anchor, parsed["probabilities"]),
            }
        )
    return predictions, call_records


def _mean_anchor_l1_deviation(
    anchor_prediction: dict[str, dict[str, float]],
    candidate_prediction: dict[str, dict[str, float]],
) -> float:
    values = [
        _l1(anchor, candidate_prediction[segment_key])
        for segment_key, anchor in anchor_prediction.items()
        if segment_key in candidate_prediction
    ]
    return sum(values) / len(values) if values else 0.0


def _max_anchor_l1_deviation(
    anchor_prediction: dict[str, dict[str, float]],
    candidate_prediction: dict[str, dict[str, float]],
) -> float:
    values = [
        _l1(anchor, candidate_prediction[segment_key])
        for segment_key, anchor in anchor_prediction.items()
        if segment_key in candidate_prediction
    ]
    return max(values) if values else 0.0


def _l1(left: dict[str, float], right: dict[str, float]) -> float:
    keys = sorted(set(left) | set(right))
    return sum(abs(float(left.get(key, 0.0)) - float(right.get(key, 0.0))) for key in keys)


def _overall_status(
    *,
    task_count: int,
    deterministic_closes_count: int,
    llm_copy_results: list[dict[str, Any]],
    llm_copy_closes_count: int,
) -> str:
    if llm_copy_results and llm_copy_closes_count == task_count:
        return "llm_anchor_copy_repair_positive"
    if deterministic_closes_count == task_count:
        return "hybrid_anchor_fidelity_repair_available"
    return "anchor_fidelity_repair_not_found"


def _risk_flags(
    *,
    execute_llm_copy: bool,
    llm_copy_results: list[dict[str, Any]],
) -> list[str]:
    flags = [
        "not_customer_field_validation",
        "repair_diagnostic_not_original_lcdu_prompt",
    ]
    if not execute_llm_copy:
        flags.append("llm_anchor_copy_not_executed")
    if llm_copy_results and any(
        result.get("mean_anchor_l1_deviation", 0.0) > 1e-9
        for result in llm_copy_results
    ):
        flags.append("llm_anchor_copy_deviation_observed")
    return flags


def _build_completion_fn(
    *,
    provider: str,
    model: str,
    base_url: str | None,
    timeout_seconds: float | None,
) -> CompletionFn:
    client = LLMClient(
        LLMClientConfig(
            provider=provider,
            model=model,
            base_url=base_url,
            temperature=0.0,
            max_tokens=300,
            timeout_seconds=timeout_seconds,
        )
    )
    return client.chat


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES anchor fidelity repair must be strict JSON") from exc


def anchor_json_from_prompt(prompt: str) -> dict[str, float]:
    match = re.search(r"Anchor JSON:\s*(\{.*\})", prompt)
    if not match:
        raise ValueError("prompt missing anchor JSON")
    return {key: float(value) for key, value in json.loads(match.group(1)).items()}


if __name__ == "__main__":
    raise SystemExit(main())
