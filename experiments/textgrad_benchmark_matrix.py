from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EVAL_SIZES = (1, 2, 5)
MATRIX_SCHEMA_VERSION = "circe-textgrad-matrix-v1"
MATRIX_CLAIM_BOUNDARY = (
    "bounded TextGrad benchmark matrix plan; not paper-grade TextGrad effectiveness evidence"
)


def build_matrix_plan(run_prefix: str = "textgrad-matrix") -> list[dict[str, Any]]:
    plan = []
    for eval_size in EVAL_SIZES:
        plan.append(
            {
                "run_id": f"{run_prefix}-dry-eval{eval_size}-baseline",
                "mode": "dry-run",
                "eval_size": eval_size,
                "max_iterations": 2,
                "variant": "baseline",
            }
        )
        plan.append(
            {
                "run_id": f"{run_prefix}-local-eval{eval_size}-limited",
                "mode": "local",
                "eval_size": eval_size,
                "max_iterations": 2,
                "variant": "limited",
            }
        )
    return plan


def summarize_matrix(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    improvement_ratios = [
        float(manifest.get("metrics", {}).get("improvement_ratio", 0.0))
        for manifest in manifests
    ]
    negative_result_count = sum(
        1 for manifest in manifests if _is_negative_textgrad_result(manifest)
    )
    return {
        "run_count": len(manifests),
        "best_improvement_ratio": max(improvement_ratios, default=0.0),
        "negative_result_count": negative_result_count,
    }


def write_matrix_index(
    path: str | Path,
    *,
    matrix_id: str,
    manifest_refs: list[str],
    summary: dict[str, Any] | None = None,
    claim_boundary: str = MATRIX_CLAIM_BOUNDARY,
) -> Path:
    index = {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "matrix_id": matrix_id,
        "manifest_refs": manifest_refs,
        "summary": summary or {},
        "claim_boundary": claim_boundary,
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, allow_nan=False, indent=2, sort_keys=True))
    return output_path


def _is_negative_textgrad_result(manifest: dict[str, Any]) -> bool:
    metrics = manifest.get("metrics", {})
    if metrics.get("textgrad_effect_status") == "updated_no_improvement":
        return True
    return (
        int(metrics.get("textgrad_call_count", 0)) > 0
        and int(metrics.get("prompt_update_count", 0)) > 0
        and float(metrics.get("improvement_ratio", 0.0)) <= 0.0
    )
