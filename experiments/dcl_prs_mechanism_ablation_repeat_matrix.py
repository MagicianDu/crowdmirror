from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_mechanism_ablation_matrix import (  # noqa: E402
    build_mechanism_ablation_matrix,
)
from experiments.dcl_prs_mechanism_program import (  # noqa: E402
    build_mechanism_program_index,
)


MECHANISM_ABLATION_REPEAT_SCHEMA_VERSION = (
    "dcl-prs-mechanism-ablation-repeat-matrix-v1"
)
SPLIT_SALTS = ["s0", "s1", "s2"]


def build_mechanism_ablation_repeat_matrix(
    *,
    artifact_id: str,
    mechanism_ablation_matrix: dict[str, Any],
) -> dict[str, Any]:
    _validate_mechanism_ablation_matrix(mechanism_ablation_matrix)
    repeat_cases = []
    stable_case_ids = set()
    for case_index, case in enumerate(mechanism_ablation_matrix["ablation_cases"]):
        salted_impacts = []
        for salt in SPLIT_SALTS:
            impact = _salted_impact(case["impact_abs"], salt=salt)
            salted_impacts.append(impact)
            repeat_cases.append(
                {
                    "case_id": f"{case['program_id']}::{case['ablated_mechanism_name']}",
                    "case_index": case_index,
                    "salt": salt,
                    "salted_impact_abs": impact,
                    "stable_nonzero": impact > 0.000000001,
                    "claim_status": "diagnostic_only",
                }
            )
        if all(impact > 0.000000001 for impact in salted_impacts):
            stable_case_ids.add(case_index)
    matrix = {
        "schema_version": MECHANISM_ABLATION_REPEAT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "mechanism_ablation_repeat_matrix_ready",
        "source_artifact_id": mechanism_ablation_matrix["artifact_id"],
        "split_salts": SPLIT_SALTS,
        "ablation_case_count": mechanism_ablation_matrix["ablation_case_count"],
        "repeat_case_count": len(repeat_cases),
        "stable_nonzero_case_count": len(stable_case_ids),
        "stable_nonzero_impact_rate": round(
            len(stable_case_ids) / mechanism_ablation_matrix["ablation_case_count"],
            12,
        ),
        "repeat_cases": repeat_cases,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "diagnostic_evidence_only",
        "next_gate": "run_mechanism_ablation_effect_validation",
        "risk_flags": [
            "deterministic_repeat_smoke_only",
            "not_real_split_repeat_validation",
            "not_strong_baseline_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "Mechanism ablation repeat matrix checks deterministic stability "
                "of nonzero mechanism impacts; it is not predictive validation."
            ),
        },
    }
    _assert_strict_json(matrix)
    return matrix


def write_mechanism_ablation_repeat_matrix(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-mechanism-ablation-repeat-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-current-001"
    )
    ablation = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-current-001",
        mechanism_program_index=mechanism,
    )
    matrix = build_mechanism_ablation_repeat_matrix(
        artifact_id=artifact_id,
        mechanism_ablation_matrix=ablation,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_mechanism_ablation_repeat_matrix",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-mechanism-ablation-repeat-current-001",
    )
    args = parser.parse_args()
    written = write_mechanism_ablation_repeat_matrix(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["matrix"]["overall_status"],
                "repeat_case_count": written["matrix"]["repeat_case_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _salted_impact(impact_abs: float, *, salt: str) -> float:
    adjustment = {"s0": 1.0, "s1": 0.97, "s2": 1.03}[salt]
    return round(impact_abs * adjustment, 12)


def _validate_mechanism_ablation_matrix(matrix: dict[str, Any]) -> None:
    if matrix.get("schema_version") != "dcl-prs-mechanism-ablation-matrix-v1":
        raise ValueError("mechanism_ablation_matrix has unsupported schema_version")
    if not matrix.get("ablation_cases"):
        raise ValueError("mechanism_ablation_matrix must contain ablation_cases")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
