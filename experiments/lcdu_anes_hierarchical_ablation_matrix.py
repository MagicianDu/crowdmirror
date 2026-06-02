from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.lcdu_anes_hierarchical_calibration_matrix import (
    ANCHOR_METHOD_ID,
    DEFAULT_K_GRID,
    build_lcdu_anes_hierarchical_calibration_matrix,
)
from experiments.lcdu_anes_public_microdata_ingestion import (
    ANES_SDA_ANALYSIS_URL,
    load_anes_sda_subset_rows,
)
from experiments.lcdu_anes_split_repeat_robustness_matrix import (
    DEFAULT_SPLIT_SALTS,
    _microdata_artifact_for_salt,
)


HIERARCHICAL_ABLATION_SCHEMA_VERSION = (
    "lcdu-anes-hierarchical-ablation-matrix-v1"
)
EPSILON = 1e-12


def build_lcdu_anes_hierarchical_ablation_matrix(
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
        raise ValueError("hierarchical ablation matrix requires rows")
    if not split_salts:
        raise ValueError("split_salts must not be empty")
    k_grid = k_grid or DEFAULT_K_GRID
    candidate_rows = []
    selected_rows = []
    task_ids = set()
    for split_salt in split_salts:
        microdata_artifact = _microdata_artifact_for_salt(
            rows,
            split_salt=split_salt,
        )
        hierarchical = build_lcdu_anes_hierarchical_calibration_matrix(
            microdata_artifact=microdata_artifact,
            artifact_id=f"lcdu-hierarchical-ablation-repeat-{split_salt}",
            k_grid=k_grid,
            max_worst_segment_delta=max_worst_segment_delta,
        )
        for task_id, task_result in hierarchical["task_results"].items():
            task_ids.add(task_id)
            selected_rows.append(
                _selected_row(
                    split_salt=split_salt,
                    task_id=task_id,
                    task_result=task_result,
                )
            )
            candidate_rows.extend(
                _candidate_rows(
                    split_salt=split_salt,
                    task_id=task_id,
                    task_result=task_result,
                    max_worst_segment_delta=max_worst_segment_delta,
                )
            )
    prior_family_summary = _summary_by_key(candidate_rows, key="prior_family")
    prior_family_k_summary = _prior_family_k_summary(candidate_rows)
    k_summary = _summary_by_key(
        [row for row in candidate_rows if row["k"] is not None],
        key="k",
    )
    artifact = {
        "schema_version": HIERARCHICAL_ABLATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(prior_family_summary),
        "validation_type": "lcdu_hierarchical_prior_k_ablation_matrix",
        "method_family_under_test": "LCDU-hybrid-v2-constrained",
        "source": {
            "source_file_name": source_file_name,
            "source_url": source_url,
            "source_extract_type": "sda_custom_subset_public_use_microdata",
        },
        "candidate_generation_split": "calibration",
        "candidate_acceptance_split": "heldout",
        "final_claim_check_split": "test",
        "split_salts": split_salts,
        "repeat_count": len(split_salts),
        "task_count": len(task_ids),
        "k_grid": k_grid,
        "max_worst_segment_delta": max_worst_segment_delta,
        "candidate_row_count": len(candidate_rows),
        "prior_family_summary": prior_family_summary,
        "prior_family_k_summary": prior_family_k_summary,
        "best_prior_family_k": _best_prior_family_k(prior_family_k_summary),
        "k_summary": k_summary,
        "selected_method_summary": _selected_method_summary(selected_rows),
        "task_prior_family_summary": _task_prior_family_summary(candidate_rows),
        "risk_flags": _risk_flags(prior_family_summary),
        "claim_boundary": (
            "This artifact decomposes LCDU-hybrid v2 candidate behavior by prior "
            "family and shrinkage k under repeated ANES salted splits. It is a "
            "diagnostic ablation, not a standalone accuracy claim or external "
            "validation result."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_hierarchical_ablation_matrix(
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
    artifact = build_lcdu_anes_hierarchical_ablation_matrix(
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
            "experiments/results/lcdu_hierarchical_ablation/"
            "lcdu-anes-hierarchical-ablation-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-hierarchical-ablation-current-001",
    )
    parser.add_argument("--split-salts", nargs="+", default=DEFAULT_SPLIT_SALTS)
    parser.add_argument("--k-grid", nargs="*", type=float, default=DEFAULT_K_GRID)
    parser.add_argument("--max-worst-segment-delta", type=float, default=0.0)
    parser.add_argument("--source-url", default=ANES_SDA_ANALYSIS_URL)
    args = parser.parse_args()
    written = write_lcdu_anes_hierarchical_ablation_matrix(
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
                "candidate_row_count": artifact["candidate_row_count"],
                "output": written["output_path"],
                "repeat_count": artifact["repeat_count"],
                "status": artifact["overall_status"],
                "task_count": artifact["task_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _candidate_rows(
    *,
    split_salt: str,
    task_id: str,
    task_result: dict[str, Any],
    max_worst_segment_delta: float,
) -> list[dict[str, Any]]:
    heldout_losses = task_result["heldout_loss_by_method"]
    heldout_worst_losses = task_result["heldout_worst_loss_by_method"]
    test_losses = task_result["test_loss_by_method"]
    test_worst_losses = task_result["test_worst_loss_by_method"]
    anchor_test_loss = test_losses[ANCHOR_METHOD_ID]
    anchor_test_worst = test_worst_losses[ANCHOR_METHOD_ID]
    anchor_heldout_loss = heldout_losses[ANCHOR_METHOD_ID]
    anchor_heldout_worst = heldout_worst_losses[ANCHOR_METHOD_ID]
    rows = []
    for method_id, test_loss in sorted(test_losses.items()):
        parsed = _parse_method_id(method_id)
        if parsed["prior_family"] in {"segment_anchor", "global_aggregate"}:
            continue
        test_loss_delta = test_loss - anchor_test_loss
        test_worst_delta = test_worst_losses[method_id] - anchor_test_worst
        heldout_loss_delta = heldout_losses[method_id] - anchor_heldout_loss
        heldout_worst_delta = heldout_worst_losses[method_id] - anchor_heldout_worst
        rows.append(
            {
                "split_salt": split_salt,
                "task_id": task_id,
                "method_id": method_id,
                "prior_family": parsed["prior_family"],
                "k": parsed["k"],
                "heldout_loss_delta_vs_anchor": heldout_loss_delta,
                "heldout_worst_segment_delta_vs_anchor": heldout_worst_delta,
                "test_loss_delta_vs_anchor": test_loss_delta,
                "test_worst_segment_delta_vs_anchor": test_worst_delta,
                "beats_anchor": test_loss_delta < -EPSILON,
                "test_worst_guard_pass": (
                    test_worst_delta <= max_worst_segment_delta + EPSILON
                ),
                "joint_success": (
                    test_loss_delta < -EPSILON
                    and test_worst_delta <= max_worst_segment_delta + EPSILON
                ),
            }
        )
    return rows


def _selected_row(
    *,
    split_salt: str,
    task_id: str,
    task_result: dict[str, Any],
) -> dict[str, Any]:
    method_id = task_result["constrained_selection"]["selected_method_id"]
    parsed = _parse_method_id(method_id)
    return {
        "split_salt": split_salt,
        "task_id": task_id,
        "method_id": method_id,
        "prior_family": parsed["prior_family"],
        "k": parsed["k"],
    }


def _parse_method_id(method_id: str) -> dict[str, Any]:
    if method_id == ANCHOR_METHOD_ID:
        return {"prior_family": "segment_anchor", "k": None}
    if method_id == "calibration_aggregate_prior":
        return {"prior_family": "global_aggregate", "k": None}
    prefixes = {
        "lcdu_hierarchical_global_k_": "global",
        "lcdu_hierarchical_party_k_": "party_or_ideology",
        "lcdu_hierarchical_income_k_": "income",
        "lcdu_hierarchical_neighbor_k_": "shared_axis_neighbor",
    }
    for prefix, prior_family in prefixes.items():
        if method_id.startswith(prefix):
            return {
                "prior_family": prior_family,
                "k": float(method_id.removeprefix(prefix)),
            }
    return {"prior_family": "unknown", "k": None}


def _summary_by_key(rows: list[dict[str, Any]], *, key: str) -> dict[str, Any]:
    values = sorted({row[key] for row in rows}, key=str)
    return {
        str(value): _summarize_rows([row for row in rows if row[key] == value])
        for value in values
    }


def _task_prior_family_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    task_ids = sorted({row["task_id"] for row in rows})
    return {
        task_id: _summary_by_key(
            [row for row in rows if row["task_id"] == task_id],
            key="prior_family",
        )
        for task_id in task_ids
    }


def _prior_family_k_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = sorted({(row["prior_family"], row["k"]) for row in rows}, key=str)
    summary = {}
    for prior_family, k in pairs:
        key = f"{prior_family}|k={k:g}"
        pair_rows = [
            row
            for row in rows
            if row["prior_family"] == prior_family and row["k"] == k
        ]
        summary[key] = {
            "prior_family": prior_family,
            "k": k,
            **_summarize_rows(pair_rows),
        }
    return summary


def _best_prior_family_k(summary: dict[str, Any]) -> dict[str, Any] | None:
    if not summary:
        return None
    key, value = max(
        summary.items(),
        key=lambda item: (
            item[1]["joint_success_rate"],
            item[1]["win_rate"],
            -item[1]["mean_test_loss_delta_vs_anchor"],
        ),
    )
    return {"summary_key": key, **value}


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    win_count = sum(1 for row in rows if row["beats_anchor"])
    worst_guard_pass_count = sum(1 for row in rows if row["test_worst_guard_pass"])
    joint_success_count = sum(1 for row in rows if row["joint_success"])
    return {
        "candidate_count": count,
        "win_count": win_count,
        "win_rate": _rate(win_count, count),
        "test_worst_guard_pass_count": worst_guard_pass_count,
        "test_worst_guard_pass_rate": _rate(worst_guard_pass_count, count),
        "joint_success_count": joint_success_count,
        "joint_success_rate": _rate(joint_success_count, count),
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
    }


def _selected_method_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    method_ids = sorted({row["method_id"] for row in rows})
    return {
        method_id: {
            "selected_count": len([row for row in rows if row["method_id"] == method_id]),
            "prior_family": _parse_method_id(method_id)["prior_family"],
            "k": _parse_method_id(method_id)["k"],
        }
        for method_id in method_ids
    }


def _overall_status(prior_family_summary: dict[str, Any]) -> str:
    if not prior_family_summary:
        return "hierarchical_ablation_signal_negative"
    best_joint = max(
        summary["joint_success_rate"] for summary in prior_family_summary.values()
    )
    if best_joint >= 0.8:
        return "hierarchical_ablation_signal_positive"
    if best_joint > 0:
        return "hierarchical_ablation_signal_mixed"
    return "hierarchical_ablation_signal_negative"


def _risk_flags(prior_family_summary: dict[str, Any]) -> list[str]:
    flags = [
        "not_customer_field_validation",
        "same_public_microdata_slice",
        "diagnostic_ablation_not_final_selection_gate",
    ]
    if _overall_status(prior_family_summary) != "hierarchical_ablation_signal_positive":
        flags.append("no_prior_family_reaches_strong_joint_success_threshold")
    return flags


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES hierarchical ablation matrix must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
