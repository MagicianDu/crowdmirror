from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_mechanism_program import (  # noqa: E402
    build_mechanism_program_index,
)


MECHANISM_ABLATION_SCHEMA_VERSION = "dcl-prs-mechanism-ablation-matrix-v1"


def build_mechanism_ablation_matrix(
    *,
    artifact_id: str,
    mechanism_program_index: dict[str, Any],
) -> dict[str, Any]:
    _validate_mechanism_program_index(mechanism_program_index)
    ablation_cases = []
    for program in mechanism_program_index["programs"]:
        full_shift = _program_support_shift(program["mechanisms"])
        for mechanism in program["mechanisms"]:
            remaining = [
                candidate
                for candidate in program["mechanisms"]
                if candidate["name"] != mechanism["name"]
            ]
            ablated_shift = _program_support_shift(remaining)
            impact = abs(full_shift - ablated_shift)
            ablation_cases.append(
                {
                    "program_id": program["program_id"],
                    "policy_id": program["policy_id"],
                    "ablated_mechanism_name": mechanism["name"],
                    "ablated_mechanism_direction": mechanism["direction"],
                    "full_support_shift": round(full_shift, 12),
                    "ablated_support_shift": round(ablated_shift, 12),
                    "impact_abs": round(impact, 12),
                    "impact_direction": (
                        "positive" if full_shift - ablated_shift >= 0 else "negative"
                    ),
                    "claim_status": "diagnostic_only",
                }
            )
    nonzero_cases = [
        case for case in ablation_cases if case["impact_abs"] > 0.000000001
    ]
    matrix = {
        "schema_version": MECHANISM_ABLATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "mechanism_ablation_matrix_ready",
        "source_artifact_id": mechanism_program_index["artifact_id"],
        "program_count": mechanism_program_index["program_count"],
        "ablation_case_count": len(ablation_cases),
        "nonzero_impact_count": len(nonzero_cases),
        "nonzero_impact_rate": round(len(nonzero_cases) / len(ablation_cases), 12),
        "max_impact_abs": round(
            max(case["impact_abs"] for case in ablation_cases), 12
        ),
        "ablation_cases": ablation_cases,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "diagnostic_evidence_only",
        "next_gate": "run_mechanism_ablation_repeat_matrix",
        "risk_flags": [
            "deterministic_ablation_smoke_only",
            "no_external_validation",
            "not_strong_baseline_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "Mechanism ablation shows that structured mechanisms affect "
                "computed support shifts. It does not prove predictive quality."
            ),
        },
    }
    _assert_strict_json(matrix)
    return matrix


def write_mechanism_ablation_matrix(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-mechanism-ablation-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    matrix = build_mechanism_ablation_matrix(
        artifact_id=artifact_id,
        mechanism_program_index=build_mechanism_program_index(
            artifact_id="dcl-prs-mechanism-program-current-001"
        ),
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
        default="experiments/results/dcl_prs_mechanism_ablation_matrix",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-mechanism-ablation-current-001",
    )
    args = parser.parse_args()
    written = write_mechanism_ablation_matrix(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "ablation_case_count": written["matrix"]["ablation_case_count"],
                "index": written["index_path"],
                "overall_status": written["matrix"]["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _program_support_shift(mechanisms: list[dict[str, Any]]) -> float:
    shift = 0.0
    for mechanism in mechanisms:
        direction = mechanism["direction"]
        strength = mechanism["strength"]
        if direction == "increase_support":
            shift += strength
        elif direction == "decrease_support":
            shift -= strength
        elif direction == "conditional_support":
            shift += strength * 0.15
        elif direction == "increase_uncertainty":
            shift -= strength * 0.05
    return shift / max(len(mechanisms), 1)


def _validate_mechanism_program_index(index: dict[str, Any]) -> None:
    if index.get("schema_version") != "dcl-prs-mechanism-program-index-v1":
        raise ValueError("mechanism_program_index has unsupported schema_version")
    if not index.get("programs"):
        raise ValueError("mechanism_program_index must contain programs")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
