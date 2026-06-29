from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_public_dataset_ingestion import (  # noqa: E402
    build_cross_domain_ingestion_index,
)


CROSS_DOMAIN_SMOKE_SCHEMA_VERSION = "dcl-prs-cross-domain-task-slice-smoke-v1"

FIELD_MAPPINGS: dict[str, dict[str, Any]] = {
    "gss_public_health_confidence_attitude_v1": {
        "cohort": ["age_group", "education", "income", "political_views"],
        "policy_or_question": [
            "confidence_in_medicine",
            "health_policy_attitude_family",
        ],
        "response_distribution": [
            "great_deal",
            "only_some",
            "hardly_any",
        ],
    },
    "eurobarometer_eu_policy_trust_attitude_v1": {
        "cohort": [
            "country",
            "age_group",
            "education",
            "left_right_self_placement",
        ],
        "policy_or_question": [
            "trust_in_eu",
            "eu_policy_priority_family",
        ],
        "response_distribution": [
            "tend_to_trust",
            "tend_not_to_trust",
            "dont_know",
        ],
    },
}


def build_cross_domain_task_slice_smoke(
    *,
    artifact_id: str,
    cross_domain_ingestion: dict[str, Any],
) -> dict[str, Any]:
    _validate_cross_domain_ingestion(cross_domain_ingestion)
    mappings = []
    for task_slice in cross_domain_ingestion["task_slices"]:
        task_slice_id = task_slice["task_slice_id"]
        field_mapping = FIELD_MAPPINGS[task_slice_id]
        required_fields_mapped = all(
            field_mapping.get(field_name)
            for field_name in (
                "cohort",
                "policy_or_question",
                "response_distribution",
            )
        )
        mappings.append(
            {
                "task_slice_id": task_slice_id,
                "source_id": task_slice["source_id"],
                "policy_domain": task_slice["policy_domain"],
                "field_mapping": field_mapping,
                "required_fields_mapped": required_fields_mapped,
                "mapping_status": (
                    "required_fields_mapped"
                    if required_fields_mapped
                    else "required_fields_missing"
                ),
            }
        )
    all_required = all(mapping["required_fields_mapped"] for mapping in mappings)
    smoke = {
        "schema_version": CROSS_DOMAIN_SMOKE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "cross_domain_task_slice_smoke_ready",
        "source_artifact_id": cross_domain_ingestion["artifact_id"],
        "dataset_count": cross_domain_ingestion["required_dataset_count"],
        "mapped_task_slice_count": len(mappings),
        "all_required_fields_mapped": all_required,
        "task_slice_mappings": mappings,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "not_runtime_ready",
        "next_gate": "load_cross_domain_public_microdata_slices",
        "risk_flags": [
            "field_mapping_smoke_only",
            "microdata_not_loaded",
            "not_model_quality_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "Cross-domain task-slice smoke verifies schema mapping only. "
                "It does not load public microdata or validate model quality."
            ),
        },
    }
    _assert_strict_json(smoke)
    return smoke


def write_cross_domain_task_slice_smoke(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-cross-domain-task-slice-smoke-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    smoke = build_cross_domain_task_slice_smoke(
        artifact_id=artifact_id,
        cross_domain_ingestion=build_cross_domain_ingestion_index(
            artifact_id="dcl-prs-cross-domain-ingestion-current-001"
        ),
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(smoke, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "smoke": smoke}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_cross_domain_task_slice_smoke",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-cross-domain-task-slice-smoke-current-001",
    )
    args = parser.parse_args()
    written = write_cross_domain_task_slice_smoke(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "mapped_task_slice_count": written["smoke"][
                    "mapped_task_slice_count"
                ],
                "overall_status": written["smoke"]["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_cross_domain_ingestion(index: dict[str, Any]) -> None:
    if index.get("schema_version") != "dcl-prs-cross-domain-ingestion-index-v1":
        raise ValueError("cross_domain_ingestion has unsupported schema_version")
    if not index.get("task_slices"):
        raise ValueError("cross_domain_ingestion must contain task_slices")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
