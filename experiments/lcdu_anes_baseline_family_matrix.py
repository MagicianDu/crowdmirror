from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.lcdu_anes_cross_task_validation import (
    _mix_probabilities,
    _weighted_segment_jsd,
    _worst_segment_jsd,
)


BASELINE_FAMILY_SCHEMA_VERSION = "lcdu-anes-baseline-family-matrix-v1"
LLM_VALIDATION_SCHEMA_VERSION = "lcdu-anes-llm-simulator-validation-v1"
MICRODATA_SCHEMA_VERSION = "lcdu-anes-public-microdata-ingestion-v1"
DEFAULT_POPULATION_ALPHA_GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
DEFAULT_PROMPT_OPTIMIZER_METHOD_IDS = ["raw_prompt", "aggregate_anchor_prompt"]


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_baseline_family_matrix(
    *,
    microdata_artifact: dict[str, Any],
    llm_validation_artifacts: list[dict[str, Any]],
    artifact_id: str,
    population_alpha_grid: list[float] | None = None,
    prompt_optimizer_method_ids: list[str] | None = None,
) -> dict[str, Any]:
    _validate_microdata_artifact(microdata_artifact)
    for artifact in llm_validation_artifacts:
        _validate_llm_validation_artifact(artifact)
    population_alpha_grid = population_alpha_grid or DEFAULT_POPULATION_ALPHA_GRID
    prompt_optimizer_method_ids = (
        prompt_optimizer_method_ids or DEFAULT_PROMPT_OPTIMIZER_METHOD_IDS
    )
    task_results = {}
    for task_id in sorted(microdata_artifact["target_distributions"]):
        baselines = []
        baselines.append(
            _population_search_result(
                task_id=task_id,
                splits=microdata_artifact["splits"],
                alpha_grid=population_alpha_grid,
                source_artifact_id=microdata_artifact["artifact_id"],
            )
        )
        prompt_result = _prompt_optimizer_result(
            task_id=task_id,
            llm_validation_artifacts=llm_validation_artifacts,
            method_ids=prompt_optimizer_method_ids,
        )
        if prompt_result is not None:
            baselines.append(prompt_result)
        task_results[task_id] = {
            "task_id": task_id,
            "baseline_results": baselines,
            "covered_baseline_families": sorted(
                {baseline["baseline_family"] for baseline in baselines}
            ),
        }
    covered_families = sorted(
        {
            baseline["baseline_family"]
            for task in task_results.values()
            for baseline in task["baseline_results"]
        }
    )
    artifact = {
        "schema_version": BASELINE_FAMILY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(covered_families),
        "validation_type": "lcdu_baseline_family_matrix",
        "source_artifact_ids": [
            microdata_artifact["artifact_id"],
            *[artifact["artifact_id"] for artifact in llm_validation_artifacts],
        ],
        "baseline_families": covered_families,
        "population_search": {
            "candidate_generation_split": "calibration",
            "candidate_acceptance_split": "heldout",
            "final_claim_check_split": "test",
            "alpha_grid": population_alpha_grid,
        },
        "prompt_optimizer": {
            "candidate_generation_split": "fixed_prompt_family",
            "candidate_acceptance_split": "heldout",
            "final_claim_check_split": "test",
            "method_ids": prompt_optimizer_method_ids,
            "llm_artifact_count": len(llm_validation_artifacts),
        },
        "task_count": len(task_results),
        "task_results": task_results,
        "risk_flags": _risk_flags(covered_families),
        "claim_boundary": (
            "This artifact covers missing strong-baseline families with a finite "
            "population-parameter grid and a heldout-selected prompt optimizer "
            "over non-LCDU LLM prompt methods. It is comparable under the same "
            "calibration/heldout/test split contract, but it is not customer "
            "field validation and the prompt optimizer is not a TextGrad "
            "gradient-update proof."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_baseline_family_matrix(
    output: str | Path,
    *,
    microdata_artifact_path: str | Path,
    llm_validation_artifact_paths: list[str | Path],
    artifact_id: str,
) -> dict[str, Any]:
    artifact = build_lcdu_anes_baseline_family_matrix(
        microdata_artifact=load_json_artifact(microdata_artifact_path),
        llm_validation_artifacts=[
            load_json_artifact(path) for path in llm_validation_artifact_paths
        ],
        artifact_id=artifact_id,
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
    parser.add_argument("--llm-validation-artifacts", nargs="*", default=[])
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_baseline_family/"
            "lcdu-anes-baseline-family-matrix-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-baseline-family-matrix-current-001",
    )
    args = parser.parse_args()
    written = write_lcdu_anes_baseline_family_matrix(
        args.output,
        microdata_artifact_path=args.microdata_artifact,
        llm_validation_artifact_paths=args.llm_validation_artifacts,
        artifact_id=args.artifact_id,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "baseline_families": artifact["baseline_families"],
                "output": written["output_path"],
                "status": artifact["overall_status"],
                "task_count": artifact["task_count"],
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


def _validate_llm_validation_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != LLM_VALIDATION_SCHEMA_VERSION:
        raise ValueError("llm validation artifact has unsupported schema_version")
    if artifact.get("validation_type") != "split_gated_llm_segment_simulator_smoke":
        raise ValueError("llm validation artifact has unsupported validation_type")
    if not isinstance(artifact.get("task_results"), dict):
        raise ValueError("llm validation artifact missing task_results")


def _population_search_result(
    *,
    task_id: str,
    splits: dict[str, Any],
    alpha_grid: list[float],
    source_artifact_id: str,
) -> dict[str, Any]:
    calibration = splits["calibration"]["target_distributions"][task_id]
    heldout = splits["heldout"]["target_distributions"][task_id]
    test = splits["test"]["target_distributions"][task_id]
    methods = _population_candidate_predictions(calibration, alpha_grid=alpha_grid)
    heldout_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=heldout["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    test_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=test["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    worst_segment_losses = {
        method_id: _worst_segment_jsd(
            observed_by_segment=test["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    best_method_id = min(heldout_losses, key=heldout_losses.get)
    return {
        "baseline_family": "population_search",
        "method_id": best_method_id,
        "source_artifact_id": source_artifact_id,
        "evidence_type": "structured_population_alpha_grid_search",
        "selection_split": "heldout",
        "candidate_count": len(methods),
        "heldout_loss": heldout_losses[best_method_id],
        "test_loss": test_losses[best_method_id],
        "test_worst_segment_loss": worst_segment_losses[best_method_id],
        "loss_by_method": test_losses,
    }


def _population_candidate_predictions(
    calibration: dict[str, Any],
    *,
    alpha_grid: list[float],
) -> dict[str, dict[str, dict[str, float]]]:
    overall = calibration["overall"]["policy_probabilities"]
    return {
        f"population_search_alpha_{alpha:g}": {
            segment_key: _mix_probabilities(
                segment["policy_probabilities"],
                overall,
                alpha=alpha,
            )
            for segment_key, segment in calibration["by_segment"].items()
        }
        for alpha in alpha_grid
    }


def _prompt_optimizer_result(
    *,
    task_id: str,
    llm_validation_artifacts: list[dict[str, Any]],
    method_ids: list[str],
) -> dict[str, Any] | None:
    candidates = []
    for artifact in llm_validation_artifacts:
        task = artifact.get("task_results", {}).get(task_id)
        if task is None:
            continue
        heldout_losses = task.get("heldout", {}).get("loss_by_method", {})
        test_losses = task.get("test", {}).get("loss_by_method", {})
        for method_id in method_ids:
            heldout_loss = heldout_losses.get(method_id)
            test_loss = test_losses.get(method_id)
            if not isinstance(heldout_loss, (int, float)) or not isinstance(
                test_loss, (int, float)
            ):
                continue
            candidates.append(
                {
                    "artifact_id": artifact["artifact_id"],
                    "method_id": method_id,
                    "prompt_variant": artifact.get("prompt_variant"),
                    "max_segments_per_task": artifact.get("max_segments_per_task"),
                    "segment_offset": artifact.get("segment_offset"),
                    "heldout_loss": float(heldout_loss),
                    "test_loss": float(test_loss),
                }
            )
    if not candidates:
        return None
    best = min(candidates, key=lambda candidate: candidate["heldout_loss"])
    method_id = (
        "prompt_optimizer_"
        f"{best['prompt_variant'] or 'unknown'}_"
        f"{best['method_id']}_"
        f"scale{best['max_segments_per_task'] or 'unknown'}_"
        f"offset{best['segment_offset'] if best['segment_offset'] is not None else 'unknown'}"
    )
    return {
        "baseline_family": "textgrad_or_prompt_optimizer",
        "method_id": method_id,
        "source_artifact_id": best["artifact_id"],
        "evidence_type": "heldout_prompt_variant_grid_search",
        "selection_split": "heldout",
        "candidate_count": len(candidates),
        "heldout_loss": best["heldout_loss"],
        "test_loss": best["test_loss"],
        "selected_prompt_variant": best["prompt_variant"],
        "selected_prompt_method_id": best["method_id"],
        "candidate_summaries": candidates,
    }


def _overall_status(covered_families: list[str]) -> str:
    required = {"population_search", "textgrad_or_prompt_optimizer"}
    if required.issubset(set(covered_families)):
        return "baseline_family_matrix_ready"
    return "baseline_family_matrix_partial"


def _risk_flags(covered_families: list[str]) -> list[str]:
    flags = [
        "not_customer_field_validation",
        "population_search_grid_finite",
        "prompt_optimizer_not_textgrad_gradient_update",
    ]
    if "textgrad_or_prompt_optimizer" not in covered_families:
        flags.append("prompt_optimizer_family_missing")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES baseline family matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
