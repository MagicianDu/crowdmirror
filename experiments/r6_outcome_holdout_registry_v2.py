from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_outcome_holdout_registry import build_r6_outcome_holdout_registry


R6_OUTCOME_HOLDOUT_REGISTRY_V2_SCHEMA_VERSION = "r6-outcome-holdout-registry-v2"
R6_EXTERNAL_OUTCOME_DATASET_MANIFEST_SCHEMA_VERSION = (
    "r6-external-outcome-dataset-manifest-v1"
)
R6_HOLDOUT_VALIDATION_SUMMARY_SCHEMA_VERSION = "r6-holdout-validation-summary-v1"


def build_r6_outcome_holdout_registry_v2(
    *,
    artifact_id: str,
    run_id: str,
    base_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    base_registry = base_registry or build_r6_outcome_holdout_registry(
        artifact_id=f"{artifact_id}-base-registry",
        run_id=run_id,
    )
    datasets = _datasets_from_base_registry(base_registry)
    registry = {
        "schema_version": R6_OUTCOME_HOLDOUT_REGISTRY_V2_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "holdout_registry_v2_ready_proxy_diagnostic",
        "datasets": datasets,
        "registry_summary": _dataset_summary(datasets),
        "acceptance_gates": {
            "outcome_holdout_registry_v2_present": True,
            "at_least_two_domains_present": _domain_count(datasets) >= 2,
            "all_datasets_have_claim_level": all(
                bool(dataset["allowed_claim_level"]) for dataset in datasets
            ),
            "all_metrics_source_backed": all(
                bool(dataset["source_refs"]) for dataset in datasets
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [base_registry["artifact_id"]],
        "allowed_claims": [
            (
                "The registry supports proxy-diagnostic holdout accounting across "
                "multiple public domains."
            )
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "Research 已完整支撑 Product 全部核心价值",
        ],
        "blocking_gaps": [
            "needs_real_field_outcome_or_customer_pilot",
            "needs_segment_level_field_labels",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(registry)
    return registry


def build_r6_external_outcome_dataset_manifest(
    *,
    artifact_id: str,
    run_id: str,
    registry_v2: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    registry_v2 = registry_v2 or build_r6_outcome_holdout_registry_v2(
        artifact_id=f"{artifact_id}-registry-v2",
        run_id=run_id,
    )
    datasets = registry_v2["datasets"]
    manifest = {
        "schema_version": R6_EXTERNAL_OUTCOME_DATASET_MANIFEST_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "external_outcome_dataset_manifest_proxy_diagnostic",
        "datasets": datasets,
        "manifest_summary": _dataset_summary(datasets),
        "acceptance_gates": {
            "manifest_present": True,
            "at_least_two_domains_present": _domain_count(datasets) >= 2,
            "all_datasets_source_backed": all(
                bool(dataset["source_refs"]) for dataset in datasets
            ),
            "field_outcome_validated": False,
        },
        "source_refs": [registry_v2["artifact_id"]],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(manifest)
    return manifest


def build_r6_holdout_validation_summary(
    *,
    artifact_id: str,
    run_id: str,
    external_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    external_manifest = external_manifest or build_r6_external_outcome_dataset_manifest(
        artifact_id=f"{artifact_id}-external-manifest",
        run_id=run_id,
    )
    datasets = external_manifest["datasets"]
    field_outcome_validated = any(
        dataset["field_outcome_available"] for dataset in datasets
    )
    summary = {
        "schema_version": R6_HOLDOUT_VALIDATION_SUMMARY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "holdout_validation_summary_proxy_diagnostic",
        "claim_level": "validation" if field_outcome_validated else "proxy_diagnostic",
        "holdout_summary": _dataset_summary(datasets),
        "metric_source_map": {
            "trend_direction_accuracy": [
                dataset["dataset_id"] for dataset in datasets if dataset["proxy_outcome_available"]
            ],
            "interval_coverage": [
                dataset["dataset_id"] for dataset in datasets if dataset["proxy_outcome_available"]
            ],
            "risk_ranking_quality": [
                dataset["dataset_id"] for dataset in datasets if dataset["segment_label_fields"]
            ],
            "segment_precision_recall": [
                dataset["dataset_id"] for dataset in datasets if dataset["segment_label_fields"]
            ],
        },
        "acceptance_gates": {
            "holdout_validation_summary_present": True,
            "at_least_two_domains_present": _domain_count(datasets) >= 2,
            "all_metrics_source_backed": True,
            "field_outcome_validated": field_outcome_validated,
            "runtime_default_allowed": False,
        },
        "source_refs": [external_manifest["artifact_id"]],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy_superiority_established=true",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(summary)
    return summary


def write_r6_outcome_holdout_registry_v2(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_outcome_holdout_registry_v2(**kwargs))


def _datasets_from_base_registry(base_registry: dict[str, Any]) -> list[dict[str, Any]]:
    domain_by_source = {
        "htops_cost_pressure": "public_service_cost_pressure",
        "anes_health_heldout": "health_policy_reaction",
        "anes_climate_heldout": "climate_policy_reaction",
    }
    field_map = {
        "htops_cost_pressure": {
            "static_prior_fields": ["household_cost_pressure_prior", "service_dependency"],
            "scenario_shock_fields": ["cost_increase", "service_reliability_concern"],
            "segment_label_fields": ["service_dependent_low_trust", "community_watchers"],
        },
        "anes_health_heldout": {
            "static_prior_fields": ["party_prior", "ideology_prior"],
            "scenario_shock_fields": ["rights_reduction", "trust_shock"],
            "segment_label_fields": ["rights_dependent_low_trust", "rule_watchers"],
        },
        "anes_climate_heldout": {
            "static_prior_fields": ["party_prior", "ideology_prior"],
            "scenario_shock_fields": ["rule_change", "policy_salience"],
            "segment_label_fields": ["rights_dependent_low_trust", "rule_watchers"],
        },
    }
    datasets = []
    for entry in base_registry["outcome_entries"]:
        source_key = entry["source_key"]
        dataset_fields = field_map[source_key]
        datasets.append(
            {
                "dataset_id": source_key,
                "domain": domain_by_source[source_key],
                "source_type": "public_proxy",
                "field_outcome_available": False,
                "proxy_outcome_available": True,
                "static_prior_fields": dataset_fields["static_prior_fields"],
                "scenario_shock_fields": dataset_fields["scenario_shock_fields"],
                "segment_label_fields": dataset_fields["segment_label_fields"],
                "allowed_claim_level": "proxy_diagnostic",
                "known_limitations": [
                    "not_real_customer_field_outcome",
                    "not_runtime_default_validation",
                    "segment_labels_are_proxy_or_audit_aligned",
                ],
                "source_refs": [base_registry["artifact_id"], source_key],
            }
        )
    return datasets


def _dataset_summary(datasets: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dataset_count": len(datasets),
        "domain_count": _domain_count(datasets),
        "proxy_diagnostic_count": sum(
            1 for dataset in datasets if dataset["allowed_claim_level"] == "proxy_diagnostic"
        ),
        "validation_count": sum(
            1 for dataset in datasets if dataset["allowed_claim_level"] == "validation"
        ),
        "blocked_count": sum(
            1 for dataset in datasets if dataset["allowed_claim_level"] == "blocked"
        ),
        "field_outcome_count": sum(
            1 for dataset in datasets if dataset["field_outcome_available"]
        ),
    }


def _domain_count(datasets: list[dict[str, Any]]) -> int:
    return len({dataset["domain"] for dataset in datasets})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_outcome_holdout_registry_v2(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output_path),
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
