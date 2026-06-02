from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.lcdu_anes_hierarchical_calibration_matrix import (
    DEFAULT_K_GRID,
    build_lcdu_anes_hierarchical_calibration_matrix,
)
from experiments.lcdu_anes_public_microdata_ingestion import (
    ANES_PUBLIC_MICRODATA_SCHEMA_VERSION,
    ANES_SDA_ANALYSIS_URL,
    ANES_SDA_DATASET_ID,
    TASK_BINDINGS,
    _build_task_target_distribution,
    _normalize_row,
    load_anes_sda_subset_rows,
)


SPLIT_REPEAT_SCHEMA_VERSION = "lcdu-anes-split-repeat-robustness-matrix-v1"
DEFAULT_SPLIT_SALTS = [
    "salt-001",
    "salt-002",
    "salt-003",
    "salt-004",
    "salt-005",
]


def build_lcdu_anes_split_repeat_robustness_matrix(
    *,
    rows: list[dict[str, str]],
    artifact_id: str,
    split_salts: list[str],
    k_grid: list[float] | None = None,
    max_worst_segment_delta: float = 0.0,
    source_file_name: str = "anes2024_sda_lcdu_subset.csv",
    source_url: str = ANES_SDA_ANALYSIS_URL,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("split repeat robustness matrix requires rows")
    if not split_salts:
        raise ValueError("split_salts must not be empty")
    k_grid = k_grid or DEFAULT_K_GRID
    repeat_results = [
        _evaluate_repeat(
            rows=rows,
            split_salt=split_salt,
            k_grid=k_grid,
            max_worst_segment_delta=max_worst_segment_delta,
        )
        for split_salt in split_salts
    ]
    task_summary = _task_summary(repeat_results)
    total_task_repeat_count = sum(
        summary["repeat_count"] for summary in task_summary.values()
    )
    constrained_anchor_win_repeat_count = sum(
        summary["constrained_anchor_win_count"]
        for summary in task_summary.values()
    )
    test_worst_guard_pass_repeat_count = sum(
        summary["test_worst_guard_pass_count"]
        for summary in task_summary.values()
    )
    joint_success_repeat_count = sum(
        summary["joint_success_count"] for summary in task_summary.values()
    )
    artifact = {
        "schema_version": SPLIT_REPEAT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            total_task_repeat_count=total_task_repeat_count,
            joint_success_repeat_count=joint_success_repeat_count,
        ),
        "validation_type": "lcdu_split_repeat_robustness_matrix",
        "method_family_under_test": "LCDU-hybrid-v2-constrained",
        "source": {
            "source_file_name": source_file_name,
            "source_url": source_url,
            "dataset_id": ANES_SDA_DATASET_ID,
            "source_extract_type": "sda_custom_subset_public_use_microdata",
        },
        "candidate_generation_split": "calibration",
        "candidate_acceptance_split": "heldout",
        "final_claim_check_split": "test",
        "split_assignment_method": "sha256_salted_modulo",
        "split_modulus": 5,
        "split_salts": split_salts,
        "repeat_count": len(repeat_results),
        "k_grid": k_grid,
        "max_worst_segment_delta": max_worst_segment_delta,
        "total_task_repeat_count": total_task_repeat_count,
        "constrained_anchor_win_repeat_count": constrained_anchor_win_repeat_count,
        "test_worst_guard_pass_repeat_count": test_worst_guard_pass_repeat_count,
        "joint_success_repeat_count": joint_success_repeat_count,
        "joint_success_rate": _rate(
            joint_success_repeat_count,
            total_task_repeat_count,
        ),
        "task_summary": task_summary,
        "repeat_results": repeat_results,
        "risk_flags": _risk_flags(
            total_task_repeat_count=total_task_repeat_count,
            joint_success_repeat_count=joint_success_repeat_count,
            test_worst_guard_pass_repeat_count=test_worst_guard_pass_repeat_count,
        ),
        "claim_boundary": (
            "This artifact evaluates LCDU-hybrid v2 constrained calibration under "
            "multiple salted split assignments for the same ANES public-use slice. "
            "It checks split robustness of weighted loss improvement and test "
            "worst-segment guard behavior, but it is not external dataset "
            "validation, customer field validation, or proof of cross-domain "
            "generalization."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_split_repeat_robustness_matrix(
    output: str | Path,
    *,
    input_csv: str | Path,
    artifact_id: str,
    split_salts: list[str],
    k_grid: list[float] | None = None,
    max_worst_segment_delta: float = 0.0,
    source_url: str = ANES_SDA_ANALYSIS_URL,
) -> dict[str, Any]:
    rows = load_anes_sda_subset_rows(input_csv)
    input_path = Path(input_csv)
    artifact = build_lcdu_anes_split_repeat_robustness_matrix(
        rows=rows,
        artifact_id=artifact_id,
        split_salts=split_salts,
        k_grid=k_grid,
        max_worst_segment_delta=max_worst_segment_delta,
        source_file_name=input_path.name,
        source_url=source_url,
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
            "experiments/results/lcdu_split_repeat_robustness/"
            "lcdu-anes-split-repeat-robustness-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-split-repeat-robustness-current-001",
    )
    parser.add_argument("--split-salts", nargs="+", default=DEFAULT_SPLIT_SALTS)
    parser.add_argument("--k-grid", nargs="*", type=float, default=DEFAULT_K_GRID)
    parser.add_argument("--max-worst-segment-delta", type=float, default=0.0)
    parser.add_argument("--source-url", default=ANES_SDA_ANALYSIS_URL)
    args = parser.parse_args()
    written = write_lcdu_anes_split_repeat_robustness_matrix(
        args.output,
        input_csv=args.input_csv,
        artifact_id=args.artifact_id,
        split_salts=args.split_salts,
        k_grid=args.k_grid,
        max_worst_segment_delta=args.max_worst_segment_delta,
        source_url=args.source_url,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "joint_success_rate": artifact["joint_success_rate"],
                "output": written["output_path"],
                "repeat_count": artifact["repeat_count"],
                "status": artifact["overall_status"],
                "total_task_repeat_count": artifact["total_task_repeat_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _evaluate_repeat(
    *,
    rows: list[dict[str, str]],
    split_salt: str,
    k_grid: list[float],
    max_worst_segment_delta: float,
) -> dict[str, Any]:
    microdata_artifact = _microdata_artifact_for_salt(rows, split_salt=split_salt)
    calibration_artifact = build_lcdu_anes_hierarchical_calibration_matrix(
        microdata_artifact=microdata_artifact,
        artifact_id=f"lcdu-hierarchical-calibration-repeat-{split_salt}",
        k_grid=k_grid,
        max_worst_segment_delta=max_worst_segment_delta,
    )
    return {
        "split_salt": split_salt,
        "microdata_artifact_id": microdata_artifact["artifact_id"],
        "hierarchical_artifact_id": calibration_artifact["artifact_id"],
        "split_row_counts": {
            split_name: split["row_count"]
            for split_name, split in microdata_artifact["splits"].items()
        },
        "overall_status": calibration_artifact["overall_status"],
        "constrained_anchor_win_task_count": calibration_artifact[
            "constrained_anchor_win_task_count"
        ],
        "task_count": calibration_artifact["task_count"],
        "task_results": {
            task_id: _repeat_task_result(task_result)
            for task_id, task_result in calibration_artifact[
                "task_results"
            ].items()
        },
    }


def _microdata_artifact_for_salt(
    rows: list[dict[str, str]],
    *,
    split_salt: str,
) -> dict[str, Any]:
    normalized_rows = [_normalize_row(row) for row in rows]
    for row in normalized_rows:
        row["split"] = _assign_split_with_salt(row["case_id"], split_salt=split_salt)
    target_distributions = {
        task_id: _build_task_target_distribution(
            normalized_rows=normalized_rows,
            task_id=task_id,
        )
        for task_id in TASK_BINDINGS
    }
    split_projection = {
        split_name: _split_projection(
            normalized_rows=[
                row for row in normalized_rows if row["split"] == split_name
            ]
        )
        for split_name in ("calibration", "heldout", "test")
    }
    return {
        "schema_version": ANES_PUBLIC_MICRODATA_SCHEMA_VERSION,
        "artifact_id": f"lcdu-anes-public-microdata-split-{split_salt}",
        "overall_status": (
            "segment_target_distributions_materialized_with_salted_split"
        ),
        "target_distributions": target_distributions,
        "split_contract": {
            "assignment_field": "V240001",
            "assignment_method": "sha256_salted_modulo",
            "split_salt": split_salt,
            "modulus": 5,
            "candidate_generation": {
                "split_name": "calibration",
                "remainders": [0, 1, 2],
            },
            "candidate_acceptance": {
                "split_name": "heldout",
                "remainders": [3],
            },
            "final_claim_check": {
                "split_name": "test",
                "remainders": [4],
            },
        },
        "splits": split_projection,
    }


def _split_projection(normalized_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_count": len(normalized_rows),
        "unique_case_id_count": len({row["case_id"] for row in normalized_rows}),
        "task_target_valid_n": {
            task_id: sum(
                1
                for row in normalized_rows
                if row["targets"][binding["target_variable_id"]] in {1, 2, 3, 4, 5, 6, 7}
            )
            for task_id, binding in TASK_BINDINGS.items()
        },
        "target_distributions": {
            task_id: _build_task_target_distribution(
                normalized_rows=normalized_rows,
                task_id=task_id,
            )
            for task_id in TASK_BINDINGS
        },
    }


def _assign_split_with_salt(case_id: str, *, split_salt: str) -> str:
    digest_input = f"{split_salt}:{case_id}".encode("utf-8")
    remainder = int(hashlib.sha256(digest_input).hexdigest(), 16) % 5
    if remainder in {0, 1, 2}:
        return "calibration"
    if remainder == 3:
        return "heldout"
    return "test"


def _repeat_task_result(task_result: dict[str, Any]) -> dict[str, Any]:
    constrained = task_result["constrained_selection"]
    unconstrained = task_result["unconstrained_selection"]
    return {
        "unconstrained_selected_method_id": unconstrained["selected_method_id"],
        "constrained_selected_method_id": constrained["selected_method_id"],
        "constrained_fallback_reason": constrained["fallback_reason"],
        "constrained_beats_anchor": constrained["beats_deterministic_anchor"],
        "test_worst_guard_pass": constrained["test_worst_guard_pass"],
        "joint_success": (
            constrained["beats_deterministic_anchor"]
            and constrained["test_worst_guard_pass"]
        ),
        "test_loss_delta_vs_anchor": constrained["test_loss_delta_vs_anchor"],
        "test_worst_segment_delta_vs_anchor": constrained[
            "test_worst_segment_delta_vs_anchor"
        ],
        "method_interpretation": task_result["method_interpretation"],
    }


def _task_summary(repeat_results: list[dict[str, Any]]) -> dict[str, Any]:
    task_ids = sorted(
        {
            task_id
            for repeat in repeat_results
            for task_id in repeat["task_results"]
        }
    )
    return {
        task_id: _summarize_task(
            [
                repeat["task_results"][task_id]
                for repeat in repeat_results
                if task_id in repeat["task_results"]
            ]
        )
        for task_id in task_ids
    }


def _summarize_task(rows: list[dict[str, Any]]) -> dict[str, Any]:
    repeat_count = len(rows)
    constrained_anchor_win_count = sum(
        1 for row in rows if row["constrained_beats_anchor"]
    )
    test_worst_guard_pass_count = sum(
        1 for row in rows if row["test_worst_guard_pass"]
    )
    joint_success_count = sum(1 for row in rows if row["joint_success"])
    return {
        "repeat_count": repeat_count,
        "constrained_anchor_win_count": constrained_anchor_win_count,
        "constrained_anchor_win_rate": _rate(
            constrained_anchor_win_count,
            repeat_count,
        ),
        "test_worst_guard_pass_count": test_worst_guard_pass_count,
        "test_worst_guard_pass_rate": _rate(
            test_worst_guard_pass_count,
            repeat_count,
        ),
        "joint_success_count": joint_success_count,
        "joint_success_rate": _rate(joint_success_count, repeat_count),
        "mean_test_loss_delta_vs_anchor": statistics.fmean(
            row["test_loss_delta_vs_anchor"] for row in rows
        )
        if rows
        else 0.0,
        "mean_test_worst_segment_delta_vs_anchor": statistics.fmean(
            row["test_worst_segment_delta_vs_anchor"] for row in rows
        )
        if rows
        else 0.0,
        "failure_modes": _failure_modes(rows),
    }


def _failure_modes(rows: list[dict[str, Any]]) -> list[str]:
    modes = set()
    for row in rows:
        if not row["constrained_beats_anchor"]:
            modes.add("constrained_selection_not_accuracy_positive")
        if not row["test_worst_guard_pass"]:
            modes.add("test_worst_segment_guard_failed")
        if row["constrained_fallback_reason"] is not None:
            modes.add(row["constrained_fallback_reason"])
    return sorted(modes)


def _overall_status(
    *,
    total_task_repeat_count: int,
    joint_success_repeat_count: int,
) -> str:
    if total_task_repeat_count > 0 and joint_success_repeat_count == total_task_repeat_count:
        return "split_repeat_robustness_signal_positive"
    if joint_success_repeat_count > 0:
        return "split_repeat_robustness_signal_mixed"
    return "split_repeat_robustness_signal_negative"


def _risk_flags(
    *,
    total_task_repeat_count: int,
    joint_success_repeat_count: int,
    test_worst_guard_pass_repeat_count: int,
) -> list[str]:
    flags = [
        "not_customer_field_validation",
        "same_public_microdata_slice",
        "split_repeat_count_limited",
    ]
    if joint_success_repeat_count < total_task_repeat_count:
        flags.append("split_repeat_joint_success_incomplete")
    if test_worst_guard_pass_repeat_count < total_task_repeat_count:
        flags.append("test_worst_guard_instability_observed")
    return flags


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES split repeat matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
