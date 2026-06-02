from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_cross_domain_task_slice_smoke import (  # noqa: E402
    build_cross_domain_task_slice_smoke,
)
from experiments.dcl_prs_public_dataset_ingestion import (  # noqa: E402
    build_cross_domain_ingestion_index,
)


CROSS_DOMAIN_MICRODATA_SCHEMA_VERSION = "dcl-prs-cross-domain-microdata-slices-v1"

OFFICIAL_ACCESS_RECORDS = {
    "gss": {
        "source_id": "gss",
        "official_source_name": "General Social Survey",
        "official_access_url": "https://gssdataexplorer.norc.org/gss_data",
        "public_use_file_status": "available_via_gss_data_explorer",
        "download_status": "not_downloaded_in_current_artifact",
    },
    "eurobarometer": {
        "source_id": "eurobarometer",
        "official_source_name": "Eurobarometer Data Service",
        "official_access_url": (
            "https://www.gesis.org/en/eurobarometer-data-service/"
            "data-and-documentation"
        ),
        "public_use_file_status": "available_via_gesis_data_catalogue",
        "download_status": "not_downloaded_in_current_artifact",
    },
}


def build_cross_domain_microdata_access_audit(
    *,
    artifact_id: str,
    cross_domain_task_slice_smoke: dict[str, Any],
) -> dict[str, Any]:
    _validate_cross_domain_task_slice_smoke(cross_domain_task_slice_smoke)
    source_ids = [
        mapping["source_id"]
        for mapping in cross_domain_task_slice_smoke["task_slice_mappings"]
    ]
    access_records = [OFFICIAL_ACCESS_RECORDS[source_id] for source_id in source_ids]
    schema_sample_slices = [
        {
            "source_id": mapping["source_id"],
            "task_slice_id": mapping["task_slice_id"],
            "sample_slice_type": "schema_fixture_not_official_microdata",
            "field_names": sorted(mapping["field_mapping"].keys()),
            "row_count": 0,
            "official_microdata_loaded": False,
        }
        for mapping in cross_domain_task_slice_smoke["task_slice_mappings"]
    ]
    audit = {
        "schema_version": CROSS_DOMAIN_MICRODATA_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "cross_domain_microdata_access_audit_ready",
        "source_artifact_id": cross_domain_task_slice_smoke["artifact_id"],
        "official_source_ids": source_ids,
        "official_access_records": access_records,
        "official_microdata_loaded": False,
        "sample_slice_type": "schema_fixture_not_official_microdata",
        "schema_sample_slices": schema_sample_slices,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "not_runtime_ready",
        "next_gate": "download_official_cross_domain_public_use_files",
        "risk_flags": [
            "official_microdata_not_downloaded",
            "schema_fixture_only",
            "not_model_quality_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "This artifact records official microdata access paths and "
                "schema sample slices only. It does not claim that GSS or "
                "Eurobarometer public-use microdata files were downloaded."
            ),
        },
    }
    _assert_strict_json(audit)
    return audit


def write_cross_domain_microdata_access_audit(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-cross-domain-microdata-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    ingestion = build_cross_domain_ingestion_index(
        artifact_id="dcl-prs-cross-domain-ingestion-current-001"
    )
    smoke = build_cross_domain_task_slice_smoke(
        artifact_id="dcl-prs-cross-domain-task-slice-smoke-current-001",
        cross_domain_ingestion=ingestion,
    )
    audit = build_cross_domain_microdata_access_audit(
        artifact_id=artifact_id,
        cross_domain_task_slice_smoke=smoke,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "audit": audit}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_cross_domain_microdata_slices",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-cross-domain-microdata-current-001",
    )
    args = parser.parse_args()
    written = write_cross_domain_microdata_access_audit(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "official_microdata_loaded": written["audit"][
                    "official_microdata_loaded"
                ],
                "overall_status": written["audit"]["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_cross_domain_task_slice_smoke(smoke: dict[str, Any]) -> None:
    if smoke.get("schema_version") != "dcl-prs-cross-domain-task-slice-smoke-v1":
        raise ValueError("cross_domain_task_slice_smoke has unsupported schema")
    if not smoke.get("task_slice_mappings"):
        raise ValueError("cross_domain_task_slice_smoke must contain mappings")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
