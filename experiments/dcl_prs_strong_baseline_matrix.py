from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STRONG_BASELINE_SCHEMA_VERSION = "dcl-prs-strong-baseline-matrix-v1"


def build_dcl_prs_strong_baseline_matrix(
    *,
    artifact_id: str,
) -> dict[str, Any]:
    matrix = {
        "schema_version": STRONG_BASELINE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "strong_baseline_dcl_prs_not_leading",
        "paper_gate_eligible": False,
        "covered_baseline_families": [
            "deterministic_anchor",
            "LCDU-LCR-SG",
            "fixed_party_or_ideology_prior",
            "DCL-PRS",
        ],
        "dcl_prs_leads_covered_baselines": False,
        "baseline_results": [
            {
                "baseline_family": "deterministic_anchor",
                "comparison_status": "reference_baseline_ready",
                "dcl_prs_beats_baseline": None,
            },
            {
                "baseline_family": "LCDU-LCR-SG",
                "comparison_status": "not_beaten_without_effect_validation",
                "dcl_prs_beats_baseline": False,
            },
            {
                "baseline_family": "fixed_party_or_ideology_prior",
                "comparison_status": "not_beaten_without_real_microdata",
                "dcl_prs_beats_baseline": False,
            },
        ],
        "l2_readiness": {
            "mechanism_ablation_repeat_ready": True,
            "repair_effect_validation_ready": True,
            "cross_domain_access_audit_ready": True,
            "product_runtime_manifest_ready": True,
        },
        "blocking_gaps": [
            "official_cross_domain_microdata_not_loaded",
            "real_effect_validation_missing",
            "multi_dataset_generalization_missing",
            "strong_baseline_win_missing",
        ],
        "risk_flags": [
            "readiness_not_accuracy",
            "not_multi_dataset_effect_evidence",
            "not_paper_gate_eligible",
        ],
        "claim_boundary": {
            "summary": (
                "DCL-PRS L2 has a stronger evidence chain, but it has not yet "
                "shown accuracy superiority over LCDU-LCR-SG or fixed party prior."
            )
        },
    }
    _assert_strict_json(matrix)
    return matrix


def write_dcl_prs_strong_baseline_matrix(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-strong-baseline-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    matrix = build_dcl_prs_strong_baseline_matrix(artifact_id=artifact_id)
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_strong_baseline_matrix",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-strong-baseline-current-001",
    )
    args = parser.parse_args()
    written = write_dcl_prs_strong_baseline_matrix(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["matrix"]["overall_status"],
                "paper_gate_eligible": written["matrix"]["paper_gate_eligible"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
