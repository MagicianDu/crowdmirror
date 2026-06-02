from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PUBLIC_DATASET_AUDIT_SCHEMA_VERSION = "dcl-prs-public-dataset-audit-v1"
CROSS_DOMAIN_INDEX_SCHEMA_VERSION = "dcl-prs-cross-domain-ingestion-index-v1"

PUBLIC_DATASET_AUDIT_ARTIFACT_ID = "dcl-prs-public-dataset-audit-current-001"

REQUIRED_SOURCE_IDS = ["gss", "eurobarometer"]
BACKUP_SOURCE_IDS = ["wvs"]

SOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "gss": {
        "source_id": "gss",
        "source_name": "General Social Survey",
        "source_url": "https://www.norc.org/research/projects/gss.html",
        "official_access_channel": "NORC GSS Data Explorer and public-use files",
        "domain": "us_social_attitudes",
        "coverage": [
            "institutional_trust",
            "public_health",
            "economy",
            "civil_rights",
            "social_policy",
        ],
        "source_role": "required_cross_domain_source",
        "first_l0_task_slice_id": "gss_public_health_confidence_attitude_v1",
    },
    "eurobarometer": {
        "source_id": "eurobarometer",
        "source_name": "Eurobarometer",
        "source_url": "https://www.gesis.org/en/eurobarometer-data-service",
        "official_access_channel": "GESIS Eurobarometer Data Service",
        "domain": "european_public_opinion",
        "coverage": [
            "eu_policy_trust",
            "political_attitudes",
            "social_policy",
            "migration",
            "environment",
        ],
        "source_role": "required_cross_domain_source",
        "first_l0_task_slice_id": "eurobarometer_eu_policy_trust_attitude_v1",
    },
    "wvs": {
        "source_id": "wvs",
        "source_name": "World Values Survey",
        "source_url": "https://www.worldvaluessurvey.org/WVSContents.jsp?CMSID=Documentation",
        "official_access_channel": "World Values Survey public documentation and data access",
        "domain": "cross_cultural_values",
        "coverage": [
            "democracy",
            "trust",
            "migration",
            "social_norms",
            "cultural_values",
        ],
        "source_role": "backup_second_phase_source",
        "first_l0_task_slice_id": "wvs_cross_cultural_trust_attitude_v1",
    },
}

TASK_SLICE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "gss_public_health_confidence_attitude_v1": {
        "task_slice_id": "gss_public_health_confidence_attitude_v1",
        "source_id": "gss",
        "policy_domain": "public_health_and_institutional_confidence",
        "question_family": "public confidence and social policy attitudes",
        "required_core_fields": [
            "cohort",
            "policy_or_question",
            "response_distribution",
        ],
        "candidate_cohort_axes": [
            "age_group",
            "education",
            "income",
            "political_views",
        ],
        "l0_mapping_status": "schema_mapping_ready_for_smoke",
        "claim_boundary": (
            "GSS L0 task slice records public-use variable family readiness; "
            "it is not a validated model-quality or CCF-A result."
        ),
    },
    "eurobarometer_eu_policy_trust_attitude_v1": {
        "task_slice_id": "eurobarometer_eu_policy_trust_attitude_v1",
        "source_id": "eurobarometer",
        "policy_domain": "eu_policy_trust_and_public_opinion",
        "question_family": "EU policy trust and public priorities",
        "required_core_fields": [
            "cohort",
            "policy_or_question",
            "response_distribution",
        ],
        "candidate_cohort_axes": [
            "country",
            "age_group",
            "education",
            "left_right_self_placement",
        ],
        "l0_mapping_status": "schema_mapping_ready_for_smoke",
        "claim_boundary": (
            "Eurobarometer L0 task slice records public-use variable family "
            "readiness; it is not a validated model-quality or CCF-A result."
        ),
    },
}


def build_cross_domain_dataset_audit() -> dict[str, Any]:
    sources = [SOURCE_DEFINITIONS[source_id] for source_id in REQUIRED_SOURCE_IDS]
    backup_sources = [SOURCE_DEFINITIONS[source_id] for source_id in BACKUP_SOURCE_IDS]
    audit = {
        "schema_version": PUBLIC_DATASET_AUDIT_SCHEMA_VERSION,
        "artifact_id": PUBLIC_DATASET_AUDIT_ARTIFACT_ID,
        "overall_status": "cross_domain_public_sources_audited",
        "required_source_count": len(sources),
        "required_source_ids": REQUIRED_SOURCE_IDS,
        "backup_source_ids": BACKUP_SOURCE_IDS,
        "sources": sources,
        "backup_sources": backup_sources,
        "audit_scope": {
            "license_or_access_checked": True,
            "official_source_url_recorded": True,
            "codebook_binding_completed": False,
            "microdata_downloaded": False,
            "task_slice_smoke_completed": False,
        },
        "risk_flags": [
            "not_model_quality_evidence",
            "codebook_binding_pending",
            "microdata_not_downloaded",
            "cross_domain_smoke_only",
        ],
        "claim_boundary": {
            "ccf_a_claim_status": "not_claimable",
            "product_claim_status": "source_audit_only",
            "summary": (
                "This audit records official public-source candidates and first "
                "task-slice mappings only; it does not validate model quality."
            ),
        },
    }
    _assert_strict_json(audit)
    return audit


def build_cross_domain_ingestion_index(*, artifact_id: str) -> dict[str, Any]:
    task_slices = [
        TASK_SLICE_DEFINITIONS[
            SOURCE_DEFINITIONS[source_id]["first_l0_task_slice_id"]
        ]
        for source_id in REQUIRED_SOURCE_IDS
    ]
    index = {
        "schema_version": CROSS_DOMAIN_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "cross_domain_task_slices_ready_for_smoke",
        "required_dataset_count": len(REQUIRED_SOURCE_IDS),
        "required_source_ids": REQUIRED_SOURCE_IDS,
        "backup_source_ids": BACKUP_SOURCE_IDS,
        "task_slice_count": len(task_slices),
        "task_slice_ids": [task_slice["task_slice_id"] for task_slice in task_slices],
        "task_slices": task_slices,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "not_demo_ready",
        "next_gate": "run_cross_domain_task_slice_smoke",
        "risk_flags": [
            "cross_domain_smoke_only",
            "codebook_binding_pending",
            "not_model_quality_evidence",
            "not_product_runtime_evidence",
        ],
        "claim_boundary": (
            "Cross-domain ingestion index only proves that two public source "
            "families have runnable task-slice mappings. It does not close "
            "research or product gates."
        ),
    }
    _assert_strict_json(index)
    return index


def write_cross_domain_ingestion_artifacts(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-cross-domain-ingestion-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    audit = build_cross_domain_dataset_audit()
    index = build_cross_domain_ingestion_index(artifact_id=artifact_id)

    audit_path = output_path / f"{PUBLIC_DATASET_AUDIT_ARTIFACT_ID}.json"
    index_path = output_path / f"{artifact_id}.json"
    audit_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"audit_path": str(audit_path), "index_path": str(index_path), "index": index}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_public_dataset_ingestion",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-cross-domain-ingestion-current-001",
    )
    args = parser.parse_args()

    written = write_cross_domain_ingestion_artifacts(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "audit": written["audit_path"],
                "index": written["index_path"],
                "task_slice_count": written["index"]["task_slice_count"],
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
