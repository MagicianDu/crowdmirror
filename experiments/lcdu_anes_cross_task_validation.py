from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


CROSS_TASK_VALIDATION_SCHEMA_VERSION = "lcdu-anes-cross-task-validation-v1"
MICRODATA_SCHEMA_VERSION = "lcdu-anes-public-microdata-ingestion-v1"
DEFAULT_ALPHA_GRID = [0.25, 0.5, 0.75, 1.0]
EPSILON = 1e-12


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_cross_task_validation_artifact(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    alpha_grid: list[float] | None = None,
) -> dict[str, Any]:
    _validate_microdata_artifact(microdata_artifact)
    alpha_grid = alpha_grid or DEFAULT_ALPHA_GRID
    task_results = {
        task_id: _evaluate_task(
            task_id=task_id,
            splits=microdata_artifact["splits"],
            alpha_grid=alpha_grid,
        )
        for task_id in sorted(microdata_artifact["target_distributions"])
    }
    accepted_task_count = sum(
        1 for result in task_results.values() if result["candidate_accepted"]
    )
    test_improvement_task_count = sum(
        1
        for result in task_results.values()
        if result["test"]["final_loss"] < result["test"]["initial_loss"]
    )
    artifact = {
        "schema_version": CROSS_TASK_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            accepted_task_count=accepted_task_count,
            test_improvement_task_count=test_improvement_task_count,
            task_count=len(task_results),
        ),
        "source_artifact_id": microdata_artifact["artifact_id"],
        "validation_type": "split_gated_segment_anchor_transfer_smoke",
        "loss_metric": "weighted_choice_distribution_jsd",
        "candidate_generation_split": "calibration",
        "candidate_acceptance_split": "heldout",
        "final_claim_check_split": "test",
        "candidate_family": {
            "initial_method_id": "calibration_aggregate_prior",
            "candidate_method_ids": [
                "uniform_prior",
                "calibration_segment_anchor",
                *[
                    f"lcdu_smoothed_segment_anchor_alpha_{alpha:g}"
                    for alpha in alpha_grid
                ],
            ],
            "lcdU_component_under_test": (
                "calibration-derived segment anchors and constraint smoothing; "
                "not LLM runtime simulation"
            ),
        },
        "task_count": len(task_results),
        "accepted_task_count": accepted_task_count,
        "test_improvement_task_count": test_improvement_task_count,
        "task_results": task_results,
        "risk_flags": [
            "not_llm_simulator_validation",
            "not_cross_provider_validation",
            "segment_schema_partial_coverage",
            "anchor_transfer_only",
        ],
        "claim_boundary": (
            "This artifact tests whether calibration-derived LCDU-style segment "
            "anchors transfer from heldout to test across ANES public tasks. It "
            "does not validate an LLM simulator, prompt update, provider "
            "generalization, or field prediction."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_cross_task_validation_artifact(
    output: str | Path,
    *,
    microdata_artifact_path: str | Path,
    artifact_id: str = "lcdu-anes-cross-task-validation-current-001",
) -> dict[str, Any]:
    artifact = build_lcdu_anes_cross_task_validation_artifact(
        microdata_artifact=load_json_artifact(microdata_artifact_path),
        artifact_id=artifact_id,
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
        "--microdata-artifact",
        default=(
            "experiments/results/lcdu_public_task_microdata/"
            "lcdu-anes-2024-sda-public-microdata-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_cross_task_validation/"
            "lcdu-anes-cross-task-validation-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-cross-task-validation-current-001",
    )
    args = parser.parse_args()
    written = write_lcdu_anes_cross_task_validation_artifact(
        args.output,
        microdata_artifact_path=args.microdata_artifact,
        artifact_id=args.artifact_id,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "accepted_task_count": artifact["accepted_task_count"],
                "artifact_id": artifact["artifact_id"],
                "output": written["output_path"],
                "status": artifact["overall_status"],
                "task_count": artifact["task_count"],
                "test_improvement_task_count": artifact[
                    "test_improvement_task_count"
                ],
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
    for split_name, split in artifact["splits"].items():
        if "target_distributions" not in split:
            raise ValueError(f"{split_name} split missing target distributions")


def _evaluate_task(
    *,
    task_id: str,
    splits: dict[str, Any],
    alpha_grid: list[float],
) -> dict[str, Any]:
    calibration = splits["calibration"]["target_distributions"][task_id]
    heldout = splits["heldout"]["target_distributions"][task_id]
    test = splits["test"]["target_distributions"][task_id]
    methods = _candidate_predictions(calibration, alpha_grid=alpha_grid)
    heldout_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=heldout["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    heldout_worst = {
        method_id: _worst_segment_jsd(
            observed_by_segment=heldout["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    initial_method_id = "calibration_aggregate_prior"
    initial_loss = heldout_losses[initial_method_id]
    best_method_id = min(heldout_losses, key=heldout_losses.get)
    best_loss = heldout_losses[best_method_id]
    candidate_accepted = best_method_id != initial_method_id and best_loss < initial_loss
    final_method_id = best_method_id if candidate_accepted else initial_method_id
    test_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=test["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    test_worst = {
        method_id: _worst_segment_jsd(
            observed_by_segment=test["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    return {
        "task_id": task_id,
        "target_variable_id": calibration["target_variable_id"],
        "candidate_accepted": candidate_accepted,
        "accepted_method_id": final_method_id if candidate_accepted else None,
        "acceptance_reason": (
            "heldout_loss_improved"
            if candidate_accepted
            else "no_candidate_improved_heldout_loss"
        ),
        "heldout": {
            "initial_loss": initial_loss,
            "best_loss": best_loss,
            "final_loss": heldout_losses[final_method_id],
            "initial_worst_segment_loss": heldout_worst[initial_method_id],
            "best_worst_segment_loss": heldout_worst[best_method_id],
            "final_worst_segment_loss": heldout_worst[final_method_id],
            "best_method_id": best_method_id,
            "loss_by_method": heldout_losses,
        },
        "test": {
            "initial_loss": test_losses[initial_method_id],
            "best_candidate_loss": test_losses[best_method_id],
            "final_loss": test_losses[final_method_id],
            "initial_worst_segment_loss": test_worst[initial_method_id],
            "final_worst_segment_loss": test_worst[final_method_id],
            "final_method_id": final_method_id,
            "loss_by_method": test_losses,
        },
        "segment_coverage": calibration["segment_schema_coverage"],
        "segment_count": len(calibration["by_segment"]),
        "policy_options": list(calibration["overall"]["policy_probabilities"]),
    }


def _candidate_predictions(
    calibration: dict[str, Any],
    *,
    alpha_grid: list[float],
) -> dict[str, dict[str, dict[str, float]]]:
    overall = calibration["overall"]["policy_probabilities"]
    by_segment = calibration["by_segment"]
    policy_options = list(overall)
    uniform = {policy_option: 1.0 / len(policy_options) for policy_option in policy_options}
    methods = {
        "uniform_prior": {
            segment_key: uniform
            for segment_key in by_segment
        },
        "calibration_aggregate_prior": {
            segment_key: overall
            for segment_key in by_segment
        },
        "calibration_segment_anchor": {
            segment_key: segment["policy_probabilities"]
            for segment_key, segment in by_segment.items()
        },
    }
    for alpha in alpha_grid:
        methods[f"lcdu_smoothed_segment_anchor_alpha_{alpha:g}"] = {
            segment_key: _mix_probabilities(
                segment["policy_probabilities"],
                overall,
                alpha=alpha,
            )
            for segment_key, segment in by_segment.items()
        }
    return methods


def _weighted_segment_jsd(
    *,
    observed_by_segment: dict[str, Any],
    predicted_by_segment: dict[str, dict[str, float]],
) -> float:
    total_weight = 0.0
    weighted_loss = 0.0
    for segment_key, observed in observed_by_segment.items():
        row_count = float(observed["row_count"])
        if row_count <= 0:
            continue
        predicted = predicted_by_segment.get(segment_key)
        if predicted is None:
            predicted = _fallback_prediction(predicted_by_segment)
        weighted_loss += row_count * _jsd(observed["policy_probabilities"], predicted)
        total_weight += row_count
    return weighted_loss / total_weight if total_weight else 0.0


def _worst_segment_jsd(
    *,
    observed_by_segment: dict[str, Any],
    predicted_by_segment: dict[str, dict[str, float]],
) -> float:
    values = []
    for segment_key, observed in observed_by_segment.items():
        if int(observed["row_count"]) <= 0:
            continue
        predicted = predicted_by_segment.get(segment_key)
        if predicted is None:
            predicted = _fallback_prediction(predicted_by_segment)
        values.append(_jsd(observed["policy_probabilities"], predicted))
    return max(values) if values else 0.0


def _fallback_prediction(
    predicted_by_segment: dict[str, dict[str, float]],
) -> dict[str, float]:
    if not predicted_by_segment:
        raise ValueError("prediction set must not be empty")
    first_key = next(iter(predicted_by_segment))
    return predicted_by_segment[first_key]


def _mix_probabilities(
    left: dict[str, float],
    right: dict[str, float],
    *,
    alpha: float,
) -> dict[str, float]:
    return {
        key: alpha * left.get(key, 0.0) + (1.0 - alpha) * right.get(key, 0.0)
        for key in right
    }


def _jsd(observed: dict[str, float], predicted: dict[str, float]) -> float:
    keys = sorted(set(observed) | set(predicted))
    p = [_positive(observed.get(key, 0.0)) for key in keys]
    q = [_positive(predicted.get(key, 0.0)) for key in keys]
    p = _normalize(p)
    q = _normalize(q)
    midpoint = [(a + b) / 2.0 for a, b in zip(p, q)]
    return 0.5 * _kl(p, midpoint) + 0.5 * _kl(q, midpoint)


def _positive(value: float) -> float:
    return max(float(value), 0.0)


def _normalize(values: list[float]) -> list[float]:
    total = sum(values)
    if total <= 0:
        return [1.0 / len(values) for _ in values]
    return [value / total for value in values]


def _kl(left: list[float], right: list[float]) -> float:
    total = 0.0
    for left_value, right_value in zip(left, right):
        if left_value <= 0:
            continue
        total += left_value * math.log(left_value / max(right_value, EPSILON))
    return total


def _overall_status(
    *,
    accepted_task_count: int,
    test_improvement_task_count: int,
    task_count: int,
) -> str:
    if accepted_task_count == task_count and test_improvement_task_count == task_count:
        return "cross_task_anchor_signal_positive"
    if accepted_task_count > 0 or test_improvement_task_count > 0:
        return "cross_task_anchor_signal_mixed"
    return "cross_task_anchor_signal_negative"


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES cross-task validation must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
