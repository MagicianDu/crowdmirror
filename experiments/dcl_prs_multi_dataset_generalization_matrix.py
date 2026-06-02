from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


MULTI_DATASET_GENERALIZATION_SCHEMA_VERSION = (
    "dcl-prs-multi-dataset-generalization-matrix-v1"
)
DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH = Path(
    "experiments/results/dcl_prs_gss_real_repair_effect_validation/"
    "dcl-prs-gss-real-repair-effect-current-001.json"
)
DEFAULT_OFFICIAL_PUBLIC_USE_FILE_PROBE_PATH = Path(
    "experiments/results/dcl_prs_official_public_use_file_probe/"
    "dcl-prs-official-public-use-file-probe-current-001.json"
)


def build_multi_dataset_generalization_matrix(
    *,
    artifact_id: str,
    gss_real_repair_effect_validation: dict[str, Any],
    official_public_use_file_probe: dict[str, Any],
) -> dict[str, Any]:
    _validate_gss_real_effect(gss_real_repair_effect_validation)
    _validate_official_probe(official_public_use_file_probe)
    eurobarometer_record = official_public_use_file_probe["source_results"][
        "eurobarometer"
    ]
    source_results = {
        "gss": {
            "source_id": "gss",
            "task_slice_id": gss_real_repair_effect_validation["task_slice_id"],
            "source_artifact_id": gss_real_repair_effect_validation["artifact_id"],
            "generalization_status": "single_dataset_real_effect_ready",
            "real_effect_promoted_count": gss_real_repair_effect_validation[
                "real_effect_promoted_count"
            ],
            "accepted_candidate_count": gss_real_repair_effect_validation[
                "accepted_candidate_count"
            ],
            "valid_policy_response_count": gss_real_repair_effect_validation[
                "real_target"
            ]["valid_policy_response_count"],
        },
        "eurobarometer": {
            "source_id": "eurobarometer",
            "source_artifact_id": official_public_use_file_probe["artifact_id"],
            "generalization_status": "blocked_microdata_missing",
            "download_status": eurobarometer_record["download_status"],
            "requires_login": eurobarometer_record["requires_login"],
            "blocking_condition": eurobarometer_record["blocking_condition"],
        },
    }
    matrix = {
        "schema_version": MULTI_DATASET_GENERALIZATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "multi_dataset_generalization_partial",
        "required_source_ids": ["gss", "eurobarometer"],
        "required_dataset_count": 2,
        "available_real_effect_dataset_count": 1,
        "blocked_dataset_count": 1,
        "generalization_gate_closed": False,
        "source_results": source_results,
        "generalization_axes": [
            "source_dataset",
            "policy_domain",
            "institutional_context",
            "task_slice",
        ],
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "partial_external_validity_evidence",
        "next_gate": "complete_eurobarometer_authenticated_download",
        "risk_flags": [
            "single_real_effect_dataset_only",
            "eurobarometer_microdata_missing",
            "not_ccf_a_generalization_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "This matrix records cross-dataset generalization readiness. "
                "GSS has real target evidence, but Eurobarometer remains "
                "login-gated, so the multi-dataset generalization gate is open."
            ),
        },
    }
    _assert_strict_json(matrix)
    return matrix


def write_multi_dataset_generalization_matrix(
    *,
    gss_real_repair_effect_validation_path: str | Path,
    official_public_use_file_probe_path: str | Path,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-multi-dataset-generalization-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    gss_real_effect = json.loads(Path(gss_real_repair_effect_validation_path).read_text())
    official_probe = json.loads(Path(official_public_use_file_probe_path).read_text())
    matrix = build_multi_dataset_generalization_matrix(
        artifact_id=artifact_id,
        gss_real_repair_effect_validation=gss_real_effect,
        official_public_use_file_probe=official_probe,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gss-real-repair-effect-validation-path",
        default=str(DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH),
    )
    parser.add_argument(
        "--official-public-use-file-probe-path",
        default=str(DEFAULT_OFFICIAL_PUBLIC_USE_FILE_PROBE_PATH),
    )
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_multi_dataset_generalization_matrix",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-multi-dataset-generalization-current-001",
    )
    args = parser.parse_args()
    written = write_multi_dataset_generalization_matrix(
        gss_real_repair_effect_validation_path=(
            args.gss_real_repair_effect_validation_path
        ),
        official_public_use_file_probe_path=args.official_public_use_file_probe_path,
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "generalization_gate_closed": written["matrix"][
                    "generalization_gate_closed"
                ],
                "overall_status": written["matrix"]["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_gss_real_effect(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "dcl-prs-gss-real-repair-effect-v1":
        raise ValueError("gss_real_repair_effect_validation has unsupported schema")
    if artifact.get("overall_status") != "gss_real_repair_effect_validation_ready":
        raise ValueError("gss_real_repair_effect_validation must be ready")
    if int(artifact.get("real_effect_promoted_count", 0)) <= 0:
        raise ValueError("gss_real_repair_effect_validation must promote candidates")


def _validate_official_probe(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "dcl-prs-official-public-use-file-probe-v1":
        raise ValueError("official_public_use_file_probe has unsupported schema")
    if artifact.get("overall_status") != "official_public_use_file_probe_partial":
        raise ValueError("official_public_use_file_probe must be partial")
    if "eurobarometer" not in artifact.get("source_results", {}):
        raise ValueError("official_public_use_file_probe must include eurobarometer")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
