from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


HYBRID_METHOD_SCHEMA_VERSION = "lcdu-anes-hybrid-method-validation-v1"
STRONG_BASELINE_SCHEMA_VERSION = "lcdu-anes-strong-baseline-matrix-v1"
ANCHOR_REPAIR_SCHEMA_VERSION = "lcdu-anes-anchor-fidelity-repair-v1"
DEFAULT_PARITY_TOLERANCE = 1e-9


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_anes_hybrid_method_validation(
    *,
    artifact_id: str,
    strong_baseline_matrix: dict[str, Any],
    anchor_fidelity_repair: dict[str, Any],
    parity_tolerance: float = DEFAULT_PARITY_TOLERANCE,
) -> dict[str, Any]:
    _validate_strong_baseline_matrix(strong_baseline_matrix)
    _validate_anchor_fidelity_repair(anchor_fidelity_repair)
    task_results = {
        task_id: _task_result(
            task_id=task_id,
            strong_task=strong_task,
            repair_task=anchor_fidelity_repair["task_results"][task_id],
            parity_tolerance=parity_tolerance,
        )
        for task_id, strong_task in sorted(strong_baseline_matrix["task_results"].items())
    }
    numeric_parity_count = sum(
        1 for result in task_results.values() if result["hybrid_numeric_parity"]
    )
    strict_copy_positive_count = sum(
        1 for result in task_results.values() if result["strict_copy_positive"]
    )
    soft_loses_count = sum(
        1 for result in task_results.values() if result["soft_loses_to_best_baseline"]
    )
    artifact = {
        "schema_version": HYBRID_METHOD_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            task_count=len(task_results),
            numeric_parity_count=numeric_parity_count,
            strict_copy_positive_count=strict_copy_positive_count,
            soft_loses_count=soft_loses_count,
        ),
        "validation_type": "lcdu_hybrid_method_validation",
        "source_artifact_ids": [
            strong_baseline_matrix["artifact_id"],
            anchor_fidelity_repair["artifact_id"],
        ],
        "method_family_under_test": "LCDU-hybrid",
        "parity_tolerance": parity_tolerance,
        "task_count": len(task_results),
        "numeric_parity_count": numeric_parity_count,
        "strict_copy_positive_count": strict_copy_positive_count,
        "soft_loses_count": soft_loses_count,
        "task_results": task_results,
        "claim_boundary": (
            "LCDU-hybrid is evaluated as a constrained method candidate: numeric "
            "population distributions are produced by calibration-derived segment "
            "anchors, while the LLM is only allowed to copy or explain those "
            "anchors. This can establish numeric parity and auditability, but it "
            "is not an accuracy win over the deterministic anchor itself."
        ),
        "research_decision": _research_decision(
            task_count=len(task_results),
            numeric_parity_count=numeric_parity_count,
            strict_copy_positive_count=strict_copy_positive_count,
            soft_loses_count=soft_loses_count,
        ),
        "product_decision": _product_decision(
            task_count=len(task_results),
            numeric_parity_count=numeric_parity_count,
            strict_copy_positive_count=strict_copy_positive_count,
        ),
        "risk_flags": _risk_flags(
            task_count=len(task_results),
            numeric_parity_count=numeric_parity_count,
            soft_loses_count=soft_loses_count,
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_hybrid_method_validation(
    output: str | Path,
    *,
    artifact_id: str,
    strong_baseline_matrix_path: str | Path,
    anchor_fidelity_repair_path: str | Path,
    parity_tolerance: float = DEFAULT_PARITY_TOLERANCE,
) -> dict[str, Any]:
    artifact = build_lcdu_anes_hybrid_method_validation(
        artifact_id=artifact_id,
        strong_baseline_matrix=load_json_artifact(strong_baseline_matrix_path),
        anchor_fidelity_repair=load_json_artifact(anchor_fidelity_repair_path),
        parity_tolerance=parity_tolerance,
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
        "--strong-baseline-matrix",
        default=(
            "experiments/results/lcdu_strong_baseline/"
            "lcdu-anes-strong-baseline-matrix-anes-current-001.json"
        ),
    )
    parser.add_argument(
        "--anchor-fidelity-repair",
        default=(
            "experiments/results/lcdu_anchor_fidelity_repair/"
            "lcdu-anes-anchor-fidelity-repair-deepseek-v4-flash-copy-16seg-current-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_hybrid_method/"
            "lcdu-anes-hybrid-method-validation-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-anes-hybrid-method-validation-current-001",
    )
    parser.add_argument("--parity-tolerance", type=float, default=DEFAULT_PARITY_TOLERANCE)
    args = parser.parse_args()
    written = write_lcdu_anes_hybrid_method_validation(
        args.output,
        artifact_id=args.artifact_id,
        strong_baseline_matrix_path=args.strong_baseline_matrix,
        anchor_fidelity_repair_path=args.anchor_fidelity_repair,
        parity_tolerance=args.parity_tolerance,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "numeric_parity_count": artifact["numeric_parity_count"],
                "output": written["output_path"],
                "research_decision": artifact["research_decision"],
                "status": artifact["overall_status"],
                "strict_copy_positive_count": artifact[
                    "strict_copy_positive_count"
                ],
                "task_count": artifact["task_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_strong_baseline_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != STRONG_BASELINE_SCHEMA_VERSION:
        raise ValueError("strong baseline matrix has unsupported schema_version")
    if artifact.get("validation_type") != "lcdu_strong_baseline_matrix":
        raise ValueError("strong baseline matrix has unsupported validation_type")
    if not isinstance(artifact.get("task_results"), dict):
        raise ValueError("strong baseline matrix missing task_results")


def _validate_anchor_fidelity_repair(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != ANCHOR_REPAIR_SCHEMA_VERSION:
        raise ValueError("anchor fidelity repair has unsupported schema_version")
    if artifact.get("validation_type") != "lcdu_anchor_fidelity_repair_diagnostic":
        raise ValueError("anchor fidelity repair has unsupported validation_type")
    if not isinstance(artifact.get("task_results"), dict):
        raise ValueError("anchor fidelity repair missing task_results")


def _task_result(
    *,
    task_id: str,
    strong_task: dict[str, Any],
    repair_task: dict[str, Any],
    parity_tolerance: float,
) -> dict[str, Any]:
    best_loss = float(strong_task["best_covered_baseline_test_loss"])
    soft_loss = float(strong_task["lcdU_test_loss"])
    strict = repair_task.get("llm_anchor_copy") or repair_task[
        "deterministic_anchor_copy"
    ]
    strict_loss = float(strict["test_loss"])
    loss_delta_vs_best = strict_loss - best_loss
    loss_delta_vs_soft = strict_loss - soft_loss
    numeric_parity = abs(loss_delta_vs_best) <= parity_tolerance
    strict_copy_positive = bool(strict.get("closes_lcdu_gap")) and numeric_parity
    return {
        "task_id": task_id,
        "soft_lcdu": {
            "method_id": "LCDU-soft",
            "test_loss": soft_loss,
            "loses_to_best_baseline": soft_loss > best_loss,
            "selected_source_artifact_id": strong_task.get(
                "lcdU_selected_source_artifact_id"
            ),
        },
        "best_baseline": {
            "baseline_family": strong_task["best_covered_baseline_family"],
            "method_id": strong_task["best_covered_baseline_method_id"],
            "test_loss": best_loss,
        },
        "hybrid_candidate": {
            "method_id": "LCDU-hybrid-strict-anchor-copy",
            "test_loss": strict_loss,
            "loss_delta_vs_best_baseline": loss_delta_vs_best,
            "loss_delta_vs_soft_lcdu": loss_delta_vs_soft,
            "numeric_role": "calibration_segment_anchor_distribution",
            "llm_role": "strict_copy_or_narrative_explanation_only",
        },
        "hybrid_numeric_parity": numeric_parity,
        "strict_copy_positive": strict_copy_positive,
        "soft_loses_to_best_baseline": soft_loss > best_loss,
        "method_interpretation": (
            "hybrid_ties_best_numeric_baseline_but_does_not_beat_it"
            if numeric_parity
            else "hybrid_does_not_match_best_numeric_baseline"
        ),
    }


def _overall_status(
    *,
    task_count: int,
    numeric_parity_count: int,
    strict_copy_positive_count: int,
    soft_loses_count: int,
) -> str:
    if (
        task_count > 0
        and numeric_parity_count == task_count
        and strict_copy_positive_count == task_count
        and soft_loses_count == task_count
    ):
        return "hybrid_candidate_numeric_parity_soft_not_leading"
    if task_count > 0 and numeric_parity_count == task_count:
        return "hybrid_candidate_numeric_parity_partial_copy"
    return "hybrid_candidate_not_validated"


def _research_decision(
    *,
    task_count: int,
    numeric_parity_count: int,
    strict_copy_positive_count: int,
    soft_loses_count: int,
) -> str:
    if (
        task_count > 0
        and numeric_parity_count == task_count
        and strict_copy_positive_count == task_count
        and soft_loses_count == task_count
    ):
        return "reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win"
    if task_count > 0 and numeric_parity_count == task_count:
        return "hybrid_numeric_component_ready_llm_copy_needs_more_validation"
    return "hybrid_not_ready_as_main_contribution"


def _product_decision(
    *,
    task_count: int,
    numeric_parity_count: int,
    strict_copy_positive_count: int,
) -> str:
    if task_count > 0 and numeric_parity_count == task_count:
        if strict_copy_positive_count == task_count:
            return "adopt_hybrid_for_auditable_product_reports"
        return "adopt_deterministic_numeric_anchor_with_non_numeric_llm_narrative"
    return "do_not_adopt_hybrid_until_numeric_parity_validated"


def _risk_flags(
    *,
    task_count: int,
    numeric_parity_count: int,
    soft_loses_count: int,
) -> list[str]:
    flags = [
        "not_customer_field_validation",
        "not_accuracy_win_over_deterministic_anchor",
    ]
    if numeric_parity_count != task_count:
        flags.append("hybrid_numeric_parity_incomplete")
    if soft_loses_count:
        flags.append("soft_lcdu_not_strong_baseline_leading")
    return flags


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES hybrid method validation must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
