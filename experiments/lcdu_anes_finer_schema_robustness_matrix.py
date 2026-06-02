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
from experiments.lcdu_anes_public_microdata_ingestion import (
    ANES_SDA_ANALYSIS_URL,
    TASK_BINDINGS,
    _normalize_row,
    _policy_distribution,
    load_anes_sda_subset_rows,
)


FINER_SCHEMA_SCHEMA_VERSION = "lcdu-anes-finer-schema-robustness-matrix-v1"
DEFAULT_SCHEMA_GRID = [
    ["party_or_ideology", "income"],
    ["party_or_ideology", "income", "age"],
    ["party_or_ideology", "income", "education"],
    ["party_or_ideology", "income", "age", "education"],
]


def build_lcdu_anes_finer_schema_robustness_matrix(
    *,
    rows: list[dict[str, str]],
    artifact_id: str,
    source_file_name: str,
    source_url: str = ANES_SDA_ANALYSIS_URL,
    schema_grid: list[list[str]] | None = None,
    min_segment_rows_per_split: int = 1,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("finer schema robustness matrix requires rows")
    normalized_rows = [_normalize_row(row) for row in rows]
    schema_grid = schema_grid or DEFAULT_SCHEMA_GRID
    schema_results = [
        _evaluate_schema(
            normalized_rows=normalized_rows,
            schema_axes=schema_axes,
            min_segment_rows_per_split=min_segment_rows_per_split,
        )
        for schema_axes in schema_grid
    ]
    positive_schema_count = sum(
        1 for result in schema_results if result["schema_status"] == "schema_positive"
    )
    artifact = {
        "schema_version": FINER_SCHEMA_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            schema_count=len(schema_results),
            positive_schema_count=positive_schema_count,
        ),
        "validation_type": "lcdu_finer_schema_robustness_matrix",
        "source": {
            "source_file_name": source_file_name,
            "source_url": source_url,
            "source_extract_type": "sda_custom_subset_public_use_microdata",
        },
        "candidate_generation_split": "calibration",
        "candidate_acceptance_split": "heldout",
        "final_claim_check_split": "test",
        "loss_metric": "weighted_choice_distribution_jsd",
        "min_segment_rows_per_split": min_segment_rows_per_split,
        "schema_count": len(schema_results),
        "positive_schema_count": positive_schema_count,
        "max_axis_count": max(result["axis_count"] for result in schema_results),
        "schema_results": schema_results,
        "risk_flags": _risk_flags(schema_results),
        "claim_boundary": (
            "This matrix tests whether calibration-derived segment anchors remain "
            "positive when the ANES segment schema is refined with available "
            "public-use axes. It is still bounded by the SDA subset variables and "
            "does not cover task-card axes absent from the current slice, such as "
            "region, urbanicity, or health-insurance context."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_finer_schema_robustness_matrix(
    output: str | Path,
    *,
    input_csv: str | Path,
    artifact_id: str,
    source_url: str = ANES_SDA_ANALYSIS_URL,
    min_segment_rows_per_split: int = 1,
) -> dict[str, Any]:
    rows = load_anes_sda_subset_rows(input_csv)
    input_path = Path(input_csv)
    artifact = build_lcdu_anes_finer_schema_robustness_matrix(
        rows=rows,
        artifact_id=artifact_id,
        source_file_name=input_path.name,
        source_url=source_url,
        min_segment_rows_per_split=min_segment_rows_per_split,
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
        "--input-csv",
        default="data/raw/anes_2024/anes2024_sda_lcdu_subset.csv",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_finer_schema/"
            "lcdu-anes-finer-schema-robustness-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-finer-schema-robustness-current-001",
    )
    parser.add_argument("--source-url", default=ANES_SDA_ANALYSIS_URL)
    parser.add_argument("--min-segment-rows-per-split", type=int, default=1)
    args = parser.parse_args()
    written = write_lcdu_anes_finer_schema_robustness_matrix(
        args.output,
        input_csv=args.input_csv,
        artifact_id=args.artifact_id,
        source_url=args.source_url,
        min_segment_rows_per_split=args.min_segment_rows_per_split,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "max_axis_count": artifact["max_axis_count"],
                "output": written["output_path"],
                "positive_schema_count": artifact["positive_schema_count"],
                "schema_count": artifact["schema_count"],
                "status": artifact["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _evaluate_schema(
    *,
    normalized_rows: list[dict[str, Any]],
    schema_axes: list[str],
    min_segment_rows_per_split: int,
) -> dict[str, Any]:
    task_results = {
        task_id: _evaluate_task(
            normalized_rows=normalized_rows,
            task_id=task_id,
            schema_axes=schema_axes,
            min_segment_rows_per_split=min_segment_rows_per_split,
        )
        for task_id in sorted(TASK_BINDINGS)
    }
    positive_task_count = sum(
        1 for result in task_results.values() if result["test_improved"]
    )
    sufficient_task_count = sum(
        1 for result in task_results.values() if result["segment_count"] > 0
    )
    return {
        "schema_id": _schema_id(schema_axes),
        "schema_axes": schema_axes,
        "axis_count": len(schema_axes),
        "task_count": len(task_results),
        "sufficient_task_count": sufficient_task_count,
        "positive_task_count": positive_task_count,
        "schema_status": (
            "schema_positive"
            if positive_task_count == len(task_results)
            else "schema_mixed_or_insufficient"
        ),
        "task_results": task_results,
    }


def _evaluate_task(
    *,
    normalized_rows: list[dict[str, Any]],
    task_id: str,
    schema_axes: list[str],
    min_segment_rows_per_split: int,
) -> dict[str, Any]:
    distributions = {
        split_name: _target_distribution_for_schema(
            rows=[row for row in normalized_rows if row["split"] == split_name],
            task_id=task_id,
            schema_axes=schema_axes,
        )
        for split_name in ("calibration", "heldout", "test")
    }
    common_segments = _common_segments(
        distributions,
        min_segment_rows_per_split=min_segment_rows_per_split,
    )
    if not common_segments:
        return {
            "task_id": task_id,
            "segment_count": 0,
            "candidate_accepted": False,
            "test_improved": False,
            "status": "insufficient_common_segments",
        }
    predictions = _candidate_predictions(
        calibration=distributions["calibration"],
        selected_segments=common_segments,
    )
    heldout_selected = _filter_segments(
        distributions["heldout"]["by_segment"],
        common_segments,
    )
    test_selected = _filter_segments(distributions["test"]["by_segment"], common_segments)
    heldout_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=heldout_selected,
            predicted_by_segment=prediction,
        )
        for method_id, prediction in predictions.items()
    }
    test_losses = {
        method_id: _weighted_segment_jsd(
            observed_by_segment=test_selected,
            predicted_by_segment=prediction,
        )
        for method_id, prediction in predictions.items()
    }
    test_worst_losses = {
        method_id: _worst_segment_jsd(
            observed_by_segment=test_selected,
            predicted_by_segment=prediction,
        )
        for method_id, prediction in predictions.items()
    }
    initial_method_id = "calibration_aggregate_prior"
    candidate_method_id = "calibration_segment_anchor"
    candidate_accepted = (
        heldout_losses[candidate_method_id] < heldout_losses[initial_method_id]
    )
    test_improved = test_losses[candidate_method_id] < test_losses[initial_method_id]
    return {
        "task_id": task_id,
        "segment_count": len(common_segments),
        "selected_segments": common_segments,
        "candidate_accepted": candidate_accepted,
        "test_improved": test_improved,
        "status": "schema_task_positive" if test_improved else "schema_task_not_positive",
        "heldout": {
            "initial_loss": heldout_losses[initial_method_id],
            "candidate_loss": heldout_losses[candidate_method_id],
            "loss_by_method": heldout_losses,
        },
        "test": {
            "initial_loss": test_losses[initial_method_id],
            "candidate_loss": test_losses[candidate_method_id],
            "loss_by_method": test_losses,
            "worst_segment_loss_by_method": test_worst_losses,
        },
    }


def _target_distribution_for_schema(
    *,
    rows: list[dict[str, Any]],
    task_id: str,
    schema_axes: list[str],
) -> dict[str, Any]:
    binding = TASK_BINDINGS[task_id]
    target_variable_id = binding["target_variable_id"]
    target_rows = [
        row
        for row in rows
        if row["targets"][target_variable_id] in {1, 2, 3, 4, 5, 6, 7}
    ]
    by_segment = {}
    for segment_key in sorted(
        {_segment_key(row["axes"], schema_axes=schema_axes) for row in target_rows}
    ):
        segment_rows = [
            row
            for row in target_rows
            if _segment_key(row["axes"], schema_axes=schema_axes) == segment_key
        ]
        by_segment[segment_key] = _policy_distribution(
            values=[row["targets"][target_variable_id] for row in segment_rows],
            policy_bins=binding["policy_bins"],
        )
    return {
        "task_id": task_id,
        "target_variable_id": target_variable_id,
        "overall": _policy_distribution(
            values=[row["targets"][target_variable_id] for row in target_rows],
            policy_bins=binding["policy_bins"],
        ),
        "by_segment": by_segment,
    }


def _candidate_predictions(
    *,
    calibration: dict[str, Any],
    selected_segments: list[str],
) -> dict[str, dict[str, dict[str, float]]]:
    overall = calibration["overall"]["policy_probabilities"]
    return {
        "calibration_aggregate_prior": {
            segment_key: overall for segment_key in selected_segments
        },
        "calibration_segment_anchor": {
            segment_key: calibration["by_segment"][segment_key]["policy_probabilities"]
            for segment_key in selected_segments
        },
    }


def _common_segments(
    distributions: dict[str, dict[str, Any]],
    *,
    min_segment_rows_per_split: int,
) -> list[str]:
    common = (
        set(distributions["calibration"]["by_segment"])
        & set(distributions["heldout"]["by_segment"])
        & set(distributions["test"]["by_segment"])
    )
    return [
        segment_key
        for segment_key in sorted(common)
        if all(
            distributions[split_name]["by_segment"][segment_key]["row_count"]
            >= min_segment_rows_per_split
            for split_name in ("calibration", "heldout", "test")
        )
    ]


def _filter_segments(
    by_segment: dict[str, Any],
    selected_segments: list[str],
) -> dict[str, Any]:
    return {segment_key: by_segment[segment_key] for segment_key in selected_segments}


def _segment_key(axes: dict[str, str], *, schema_axes: list[str]) -> str:
    return "|".join(f"{axis}={axes[axis]}" for axis in schema_axes)


def _schema_id(schema_axes: list[str]) -> str:
    return "schema_" + "_".join(schema_axes)


def _overall_status(*, schema_count: int, positive_schema_count: int) -> str:
    if schema_count > 0 and positive_schema_count == schema_count:
        return "finer_schema_robustness_signal_positive"
    if positive_schema_count > 0:
        return "finer_schema_robustness_signal_mixed"
    return "finer_schema_robustness_signal_negative"


def _risk_flags(schema_results: list[dict[str, Any]]) -> list[str]:
    flags = [
        "sda_subset_not_full_raw_release_archive",
        "task_card_axes_still_partial",
    ]
    if any(result["schema_status"] != "schema_positive" for result in schema_results):
        flags.append("finer_schema_instability_or_sparsity_observed")
    if any(
        task["segment_count"] < 5
        for schema in schema_results
        for task in schema["task_results"].values()
    ):
        flags.append("sparse_common_segments_observed")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES finer schema matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
