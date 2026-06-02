from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STRONG_BASELINE_SCHEMA_VERSION = "dcl-prs-strong-baseline-matrix-v1"
DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH = Path(
    "experiments/results/dcl_prs_gss_real_repair_effect_validation/"
    "dcl-prs-gss-real-repair-effect-current-001.json"
)
DEFAULT_MULTI_DATASET_GENERALIZATION_MATRIX_PATH = Path(
    "experiments/results/dcl_prs_multi_dataset_generalization_matrix/"
    "dcl-prs-multi-dataset-generalization-current-001.json"
)


def build_dcl_prs_strong_baseline_matrix(
    *,
    artifact_id: str,
    gss_real_repair_effect_validation: dict[str, Any] | None = None,
    multi_dataset_generalization_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    real_effect_ready = _is_gss_real_effect_ready(gss_real_repair_effect_validation)
    generalization_partial = _is_generalization_partial(
        multi_dataset_generalization_matrix
    )
    blocking_gaps = [
        (
            "multi_dataset_generalization_incomplete"
            if generalization_partial
            else "multi_dataset_generalization_missing"
        ),
        "strong_baseline_win_missing",
    ]
    if not real_effect_ready:
        blocking_gaps.insert(0, "real_effect_validation_missing")
        blocking_gaps.insert(0, "official_cross_domain_microdata_not_loaded")
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
                "comparison_status": (
                    "not_beaten_without_strong_baseline_win"
                    if real_effect_ready
                    else "not_beaten_without_effect_validation"
                ),
                "dcl_prs_beats_baseline": False,
            },
            {
                "baseline_family": "fixed_party_or_ideology_prior",
                "comparison_status": (
                    "not_beaten_without_multi_dataset_generalization"
                    if real_effect_ready
                    else "not_beaten_without_real_microdata"
                ),
                "dcl_prs_beats_baseline": False,
            },
        ],
        "l2_readiness": {
            "mechanism_ablation_repeat_ready": True,
            "repair_effect_validation_ready": True,
            "cross_domain_access_audit_ready": True,
            "product_runtime_manifest_ready": True,
            "gss_real_effect_validation_ready": real_effect_ready,
            "multi_dataset_generalization_partial": generalization_partial,
        },
        "blocking_gaps": blocking_gaps,
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
    matrix = build_dcl_prs_strong_baseline_matrix(
        artifact_id=artifact_id,
        gss_real_repair_effect_validation=_load_json_if_exists(
            DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH
        ),
        multi_dataset_generalization_matrix=_load_json_if_exists(
            DEFAULT_MULTI_DATASET_GENERALIZATION_MATRIX_PATH
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


def _is_gss_real_effect_ready(artifact: dict[str, Any] | None) -> bool:
    return (
        artifact is not None
        and artifact.get("schema_version") == "dcl-prs-gss-real-repair-effect-v1"
        and artifact.get("overall_status") == "gss_real_repair_effect_validation_ready"
        and int(artifact.get("real_effect_promoted_count", 0)) > 0
    )


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _is_generalization_partial(artifact: dict[str, Any] | None) -> bool:
    return (
        artifact is not None
        and artifact.get("schema_version")
        == "dcl-prs-multi-dataset-generalization-matrix-v1"
        and artifact.get("overall_status") == "multi_dataset_generalization_partial"
        and artifact.get("generalization_gate_closed") is False
    )


if __name__ == "__main__":
    raise SystemExit(main())
