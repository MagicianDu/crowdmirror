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
    _weighted_segment_jsd,
    _worst_segment_jsd,
)


HIERARCHICAL_CALIBRATION_SCHEMA_VERSION = (
    "lcdu-anes-hierarchical-calibration-matrix-v1"
)
MICRODATA_SCHEMA_VERSION = "lcdu-anes-public-microdata-ingestion-v1"
DEFAULT_K_GRID = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0]
ANCHOR_METHOD_ID = "calibration_segment_anchor"
AGGREGATE_METHOD_ID = "calibration_aggregate_prior"
EPSILON = 1e-12


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_hierarchical_calibration_matrix(
    *,
    microdata_artifact: dict[str, Any],
    artifact_id: str,
    k_grid: list[float] | None = None,
    max_worst_segment_delta: float = 0.0,
) -> dict[str, Any]:
    _validate_microdata_artifact(microdata_artifact)
    k_grid = k_grid or DEFAULT_K_GRID
    task_results = {
        task_id: _evaluate_task(
            task_id=task_id,
            splits=microdata_artifact["splits"],
            k_grid=k_grid,
            max_worst_segment_delta=max_worst_segment_delta,
        )
        for task_id in sorted(microdata_artifact["target_distributions"])
    }
    unconstrained_anchor_win_task_count = sum(
        1
        for result in task_results.values()
        if result["unconstrained_selection"]["beats_deterministic_anchor"]
    )
    constrained_anchor_win_task_count = sum(
        1
        for result in task_results.values()
        if result["constrained_selection"]["beats_deterministic_anchor"]
    )
    constrained_worst_guard_pass_task_count = sum(
        1
        for result in task_results.values()
        if result["constrained_selection"]["heldout_worst_guard_pass"]
    )
    selected_not_oracle_count = sum(
        1
        for result in task_results.values()
        if result["selected_method_id"] != result["test_oracle_best_method_id"]
    )
    artifact = {
        "schema_version": HIERARCHICAL_CALIBRATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            task_count=len(task_results),
            anchor_win_task_count=constrained_anchor_win_task_count,
            status_prefix="hierarchical_lcdu_constrained",
        ),
        "unconstrained_overall_status": _overall_status(
            task_count=len(task_results),
            anchor_win_task_count=unconstrained_anchor_win_task_count,
            status_prefix="hierarchical_lcdu",
        ),
        "constrained_overall_status": _overall_status(
            task_count=len(task_results),
            anchor_win_task_count=constrained_anchor_win_task_count,
            status_prefix="hierarchical_lcdu_constrained",
        ),
        "source_artifact_id": microdata_artifact["artifact_id"],
        "validation_type": "lcdu_hierarchical_reliability_calibration_matrix",
        "method_family_under_test": "LCDU-hybrid-v2",
        "loss_metric": "weighted_choice_distribution_jsd",
        "candidate_generation_split": "calibration",
        "candidate_acceptance_split": "heldout",
        "final_claim_check_split": "test",
        "selection_modes": ["unconstrained", "constrained"],
        "max_worst_segment_delta": max_worst_segment_delta,
        "k_grid": k_grid,
        "candidate_family": {
            "anchor_method_id": ANCHOR_METHOD_ID,
            "prior_families": [
                "global",
                "party_or_ideology",
                "income",
                "shared_axis_neighbor",
            ],
            "unconstrained_selection_rule": "minimize_heldout_weighted_jsd",
            "constrained_selection_rule": (
                "minimize_heldout_weighted_jsd_subject_to_anchor_improvement_"
                "and_worst_segment_non_inferiority"
            ),
        },
        "task_count": len(task_results),
        "anchor_win_task_count": unconstrained_anchor_win_task_count,
        "unconstrained_anchor_win_task_count": unconstrained_anchor_win_task_count,
        "constrained_anchor_win_task_count": constrained_anchor_win_task_count,
        "constrained_worst_guard_pass_task_count": (
            constrained_worst_guard_pass_task_count
        ),
        "selected_not_oracle_count": selected_not_oracle_count,
        "task_results": task_results,
        "risk_flags": _risk_flags(
            task_count=len(task_results),
            unconstrained_anchor_win_task_count=unconstrained_anchor_win_task_count,
            constrained_anchor_win_task_count=constrained_anchor_win_task_count,
            constrained_worst_guard_pass_task_count=(
                constrained_worst_guard_pass_task_count
            ),
            selected_not_oracle_count=selected_not_oracle_count,
        ),
        "claim_boundary": (
            "This artifact evaluates LCDU-hybrid v2 as a split-gated hierarchical "
            "calibration method over public ANES segment distributions. Candidate "
            "distributions are generated only from calibration data, selected only "
            "by heldout loss, and checked on test loss. It is not customer field "
            "validation, not a live LLM simulator proof, and not evidence that the "
            "same gains hold outside the covered policy tasks."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_hierarchical_calibration_matrix(
    output: str | Path,
    *,
    microdata_artifact_path: str | Path,
    artifact_id: str,
    k_grid: list[float] | None = None,
    max_worst_segment_delta: float = 0.0,
) -> dict[str, Any]:
    artifact = build_lcdu_anes_hierarchical_calibration_matrix(
        microdata_artifact=load_json_artifact(microdata_artifact_path),
        artifact_id=artifact_id,
        k_grid=k_grid,
        max_worst_segment_delta=max_worst_segment_delta,
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
        "--output",
        default=(
            "experiments/results/lcdu_hierarchical_calibration/"
            "lcdu-anes-hierarchical-calibration-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-hierarchical-calibration-current-001",
    )
    parser.add_argument("--k-grid", nargs="*", type=float, default=DEFAULT_K_GRID)
    parser.add_argument("--max-worst-segment-delta", type=float, default=0.0)
    args = parser.parse_args()
    written = write_lcdu_anes_hierarchical_calibration_matrix(
        args.output,
        microdata_artifact_path=args.microdata_artifact,
        artifact_id=args.artifact_id,
        k_grid=args.k_grid,
        max_worst_segment_delta=args.max_worst_segment_delta,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "anchor_win_task_count": artifact["anchor_win_task_count"],
                "constrained_anchor_win_task_count": artifact[
                    "constrained_anchor_win_task_count"
                ],
                "artifact_id": artifact["artifact_id"],
                "output": written["output_path"],
                "status": artifact["overall_status"],
                "task_count": artifact["task_count"],
                "unconstrained_anchor_win_task_count": artifact[
                    "unconstrained_anchor_win_task_count"
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


def _evaluate_task(
    *,
    task_id: str,
    splits: dict[str, Any],
    k_grid: list[float],
    max_worst_segment_delta: float,
) -> dict[str, Any]:
    calibration = splits["calibration"]["target_distributions"][task_id]
    heldout = splits["heldout"]["target_distributions"][task_id]
    test = splits["test"]["target_distributions"][task_id]
    methods = _candidate_predictions(calibration, k_grid=k_grid)
    heldout_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=heldout["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    heldout_worst_losses = {
        method_id: _worst_segment_jsd(
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
    test_worst_losses = {
        method_id: _worst_segment_jsd(
            observed_by_segment=test["by_segment"],
            predicted_by_segment=prediction,
        )
        for method_id, prediction in methods.items()
    }
    selected_method_id = min(heldout_losses, key=heldout_losses.get)
    constrained_method_id, constrained_fallback_reason = _select_constrained_method(
        heldout_losses=heldout_losses,
        heldout_worst_losses=heldout_worst_losses,
        max_worst_segment_delta=max_worst_segment_delta,
    )
    test_oracle_best_method_id = min(test_losses, key=test_losses.get)
    anchor_loss = test_losses[ANCHOR_METHOD_ID]
    selected_loss = test_losses[selected_method_id]
    unconstrained_selection = _selection_summary(
        method_id=selected_method_id,
        heldout_losses=heldout_losses,
        heldout_worst_losses=heldout_worst_losses,
        test_losses=test_losses,
        test_worst_losses=test_worst_losses,
        max_worst_segment_delta=max_worst_segment_delta,
        fallback_reason=None,
    )
    constrained_selection = _selection_summary(
        method_id=constrained_method_id,
        heldout_losses=heldout_losses,
        heldout_worst_losses=heldout_worst_losses,
        test_losses=test_losses,
        test_worst_losses=test_worst_losses,
        max_worst_segment_delta=max_worst_segment_delta,
        fallback_reason=constrained_fallback_reason,
    )
    return {
        "task_id": task_id,
        "target_variable_id": calibration["target_variable_id"],
        "unconstrained_selection": unconstrained_selection,
        "constrained_selection": constrained_selection,
        "constrained_fallback_reason": constrained_fallback_reason,
        "heldout_worst_guard_pass": constrained_selection["heldout_worst_guard_pass"],
        "test_worst_guard_pass": constrained_selection["test_worst_guard_pass"],
        "method_interpretation": _method_interpretation(
            unconstrained_selection=unconstrained_selection,
            constrained_selection=constrained_selection,
        ),
        "selected_method_id": selected_method_id,
        "selected_prior_family": _selected_prior_family(selected_method_id),
        "selected_k": _selected_k(selected_method_id),
        "heldout_best_method_id": selected_method_id,
        "heldout_best_loss": heldout_losses[selected_method_id],
        "heldout_anchor_loss": heldout_losses[ANCHOR_METHOD_ID],
        "heldout_loss_delta_vs_anchor": (
            heldout_losses[selected_method_id] - heldout_losses[ANCHOR_METHOD_ID]
        ),
        "test_oracle_best_method_id": test_oracle_best_method_id,
        "test_oracle_best_loss": test_losses[test_oracle_best_method_id],
        "test_anchor_loss": anchor_loss,
        "test_final_loss": selected_loss,
        "test_loss_delta_vs_anchor": selected_loss - anchor_loss,
        "beats_deterministic_anchor": selected_loss < anchor_loss - EPSILON,
        "test_anchor_worst_segment_loss": test_worst_losses[ANCHOR_METHOD_ID],
        "test_final_worst_segment_loss": test_worst_losses[selected_method_id],
        "test_worst_segment_delta_vs_anchor": (
            test_worst_losses[selected_method_id]
            - test_worst_losses[ANCHOR_METHOD_ID]
        ),
        "heldout_anchor_worst_segment_loss": heldout_worst_losses[ANCHOR_METHOD_ID],
        "heldout_final_worst_segment_loss": heldout_worst_losses[selected_method_id],
        "candidate_method_count": len(methods),
        "heldout_loss_by_method": heldout_losses,
        "heldout_worst_loss_by_method": heldout_worst_losses,
        "test_loss_by_method": test_losses,
        "test_worst_loss_by_method": test_worst_losses,
        "segment_count": len(calibration["by_segment"]),
        "segment_coverage": calibration.get("segment_schema_coverage", {}),
        "policy_options": list(calibration["overall"]["policy_probabilities"]),
    }


def _select_constrained_method(
    *,
    heldout_losses: dict[str, float],
    heldout_worst_losses: dict[str, float],
    max_worst_segment_delta: float,
) -> tuple[str, str | None]:
    anchor_loss = heldout_losses[ANCHOR_METHOD_ID]
    anchor_worst = heldout_worst_losses[ANCHOR_METHOD_ID]
    candidates = [
        method_id
        for method_id, loss in heldout_losses.items()
        if method_id != ANCHOR_METHOD_ID
        and loss < anchor_loss - EPSILON
        and heldout_worst_losses[method_id] - anchor_worst
        <= max_worst_segment_delta + EPSILON
    ]
    if not candidates:
        return ANCHOR_METHOD_ID, "no_candidate_passed_worst_segment_guard"
    return min(candidates, key=heldout_losses.get), None


def _selection_summary(
    *,
    method_id: str,
    heldout_losses: dict[str, float],
    heldout_worst_losses: dict[str, float],
    test_losses: dict[str, float],
    test_worst_losses: dict[str, float],
    max_worst_segment_delta: float,
    fallback_reason: str | None,
) -> dict[str, Any]:
    heldout_anchor_loss = heldout_losses[ANCHOR_METHOD_ID]
    heldout_anchor_worst = heldout_worst_losses[ANCHOR_METHOD_ID]
    test_anchor_loss = test_losses[ANCHOR_METHOD_ID]
    test_anchor_worst = test_worst_losses[ANCHOR_METHOD_ID]
    heldout_worst_delta = heldout_worst_losses[method_id] - heldout_anchor_worst
    test_worst_delta = test_worst_losses[method_id] - test_anchor_worst
    test_loss_delta = test_losses[method_id] - test_anchor_loss
    return {
        "selected_method_id": method_id,
        "selected_prior_family": _selected_prior_family(method_id),
        "selected_k": _selected_k(method_id),
        "fallback_reason": fallback_reason,
        "heldout_loss": heldout_losses[method_id],
        "heldout_anchor_loss": heldout_anchor_loss,
        "heldout_loss_delta_vs_anchor": heldout_losses[method_id]
        - heldout_anchor_loss,
        "heldout_worst_segment_loss": heldout_worst_losses[method_id],
        "heldout_anchor_worst_segment_loss": heldout_anchor_worst,
        "heldout_worst_segment_delta_vs_anchor": heldout_worst_delta,
        "heldout_worst_guard_pass": (
            heldout_worst_delta <= max_worst_segment_delta + EPSILON
        ),
        "test_loss": test_losses[method_id],
        "test_anchor_loss": test_anchor_loss,
        "test_loss_delta_vs_anchor": test_loss_delta,
        "beats_deterministic_anchor": test_loss_delta < -EPSILON,
        "test_worst_segment_loss": test_worst_losses[method_id],
        "test_anchor_worst_segment_loss": test_anchor_worst,
        "test_worst_segment_delta_vs_anchor": test_worst_delta,
        "test_worst_guard_pass": (
            test_worst_delta <= max_worst_segment_delta + EPSILON
        ),
    }


def _method_interpretation(
    *,
    unconstrained_selection: dict[str, Any],
    constrained_selection: dict[str, Any],
) -> str:
    if (
        constrained_selection["beats_deterministic_anchor"]
        and constrained_selection["test_worst_guard_pass"]
    ):
        return "constrained_hierarchical_calibration_beats_anchor_without_test_worst_regression"
    if constrained_selection["beats_deterministic_anchor"]:
        return "constrained_hierarchical_calibration_beats_anchor_but_test_worst_regresses"
    if (
        unconstrained_selection["beats_deterministic_anchor"]
        and constrained_selection["selected_method_id"] == ANCHOR_METHOD_ID
    ):
        return "unconstrained_gain_blocked_by_worst_segment_guard"
    return "hierarchical_calibration_does_not_beat_anchor_under_constraint"


def _candidate_predictions(
    calibration: dict[str, Any],
    *,
    k_grid: list[float],
) -> dict[str, dict[str, dict[str, float]]]:
    overall = calibration["overall"]["policy_probabilities"]
    by_segment = calibration["by_segment"]
    methods = {
        AGGREGATE_METHOD_ID: {segment_key: overall for segment_key in by_segment},
        ANCHOR_METHOD_ID: {
            segment_key: segment["policy_probabilities"]
            for segment_key, segment in by_segment.items()
        },
    }
    for k in k_grid:
        methods[f"lcdu_hierarchical_global_k_{k:g}"] = _shrink_to_prior(
            by_segment=by_segment,
            prior_by_segment={segment_key: overall for segment_key in by_segment},
            k=k,
        )
        for prior_family, method_fragment in [
            ("party_or_ideology", "party"),
            ("income", "income"),
            ("shared_axis_neighbor", "neighbor"),
        ]:
            prior_by_segment = _neighbor_prior_by_segment(
                by_segment=by_segment,
                overall=overall,
                prior_family=prior_family,
            )
            methods[f"lcdu_hierarchical_{method_fragment}_k_{k:g}"] = (
                _shrink_to_prior(
                    by_segment=by_segment,
                    prior_by_segment=prior_by_segment,
                    k=k,
                )
            )
    return methods


def _shrink_to_prior(
    *,
    by_segment: dict[str, Any],
    prior_by_segment: dict[str, dict[str, float]],
    k: float,
) -> dict[str, dict[str, float]]:
    predictions = {}
    for segment_key, segment in by_segment.items():
        row_count = max(float(segment["row_count"]), 0.0)
        alpha = row_count / (row_count + k) if row_count + k > 0 else 0.0
        anchor = segment["policy_probabilities"]
        prior = prior_by_segment[segment_key]
        predictions[segment_key] = {
            policy_option: (
                alpha * anchor.get(policy_option, 0.0)
                + (1.0 - alpha) * prior.get(policy_option, 0.0)
            )
            for policy_option in prior
        }
    return predictions


def _neighbor_prior_by_segment(
    *,
    by_segment: dict[str, Any],
    overall: dict[str, float],
    prior_family: str,
) -> dict[str, dict[str, float]]:
    return {
        segment_key: _neighbor_prior(
            segment_key=segment_key,
            by_segment=by_segment,
            overall=overall,
            prior_family=prior_family,
        )
        for segment_key in by_segment
    }


def _neighbor_prior(
    *,
    segment_key: str,
    by_segment: dict[str, Any],
    overall: dict[str, float],
    prior_family: str,
) -> dict[str, float]:
    axes = _segment_axes(segment_key)
    matching_rows = []
    for other_segment_key, row in by_segment.items():
        if other_segment_key == segment_key:
            continue
        other_axes = _segment_axes(other_segment_key)
        if _matches_prior_family(
            axes=axes,
            other_axes=other_axes,
            prior_family=prior_family,
        ):
            matching_rows.append(row)
    return _distribution_from_counts(matching_rows, overall=overall)


def _matches_prior_family(
    *,
    axes: dict[str, str],
    other_axes: dict[str, str],
    prior_family: str,
) -> bool:
    if prior_family == "party_or_ideology":
        return (
            "party_or_ideology" in axes
            and axes["party_or_ideology"] == other_axes.get("party_or_ideology")
        )
    if prior_family == "income":
        return "income" in axes and axes["income"] == other_axes.get("income")
    if prior_family == "shared_axis_neighbor":
        return any(other_axes.get(axis) == value for axis, value in axes.items())
    raise ValueError(f"unsupported prior_family: {prior_family}")


def _distribution_from_counts(
    rows: list[dict[str, Any]],
    *,
    overall: dict[str, float],
) -> dict[str, float]:
    counts = {policy_option: 0.0 for policy_option in overall}
    for row in rows:
        for policy_option in overall:
            counts[policy_option] += float(
                row.get("policy_counts", {}).get(policy_option, 0.0)
            )
    total = sum(counts.values())
    if total <= 0:
        return overall
    return {policy_option: counts[policy_option] / total for policy_option in overall}


def _segment_axes(segment_key: str) -> dict[str, str]:
    axes = {}
    for part in segment_key.split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        axes[key] = value
    return axes


def _selected_prior_family(method_id: str) -> str:
    if method_id == ANCHOR_METHOD_ID:
        return "segment_anchor"
    if method_id == AGGREGATE_METHOD_ID:
        return "global_aggregate"
    if method_id.startswith("lcdu_hierarchical_global_k_"):
        return "global"
    if method_id.startswith("lcdu_hierarchical_party_k_"):
        return "party_or_ideology"
    if method_id.startswith("lcdu_hierarchical_income_k_"):
        return "income"
    if method_id.startswith("lcdu_hierarchical_neighbor_k_"):
        return "shared_axis_neighbor"
    return "unknown"


def _selected_k(method_id: str) -> float | None:
    marker = "_k_"
    if marker not in method_id:
        return None
    return float(method_id.rsplit(marker, 1)[1])


def _overall_status(
    *,
    task_count: int,
    anchor_win_task_count: int,
    status_prefix: str,
) -> str:
    if task_count > 0 and anchor_win_task_count == task_count:
        return f"{status_prefix}_signal_positive"
    if anchor_win_task_count > 0:
        return f"{status_prefix}_signal_mixed"
    return f"{status_prefix}_not_leading"


def _risk_flags(
    *,
    task_count: int,
    unconstrained_anchor_win_task_count: int,
    constrained_anchor_win_task_count: int,
    constrained_worst_guard_pass_task_count: int,
    selected_not_oracle_count: int,
) -> list[str]:
    flags = [
        "not_customer_field_validation",
        "not_llm_runtime_validation",
        "hierarchical_candidate_grid_finite",
        "public_microdata_slice_only",
    ]
    if unconstrained_anchor_win_task_count < task_count:
        flags.append("unconstrained_hierarchical_lcdu_not_universally_leading")
    if constrained_anchor_win_task_count < task_count:
        flags.append("constrained_hierarchical_lcdu_not_universally_leading")
    if constrained_anchor_win_task_count < unconstrained_anchor_win_task_count:
        flags.append("constrained_selection_reduced_anchor_wins")
    if constrained_worst_guard_pass_task_count < task_count:
        flags.append("constrained_worst_guard_incomplete")
    if selected_not_oracle_count > 0:
        flags.append("candidate_selected_by_heldout_not_test")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "LCDU ANES hierarchical calibration matrix must be strict JSON"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
