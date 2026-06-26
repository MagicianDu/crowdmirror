from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r10_external_evidence_registry import (
    R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_independent_holdout_data import (
    R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION,
)


R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION = (
    "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-v1"
)


def build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
    *,
    artifact_id: str,
    run_id: str,
    r12_recall_mitigation_independent_holdout_data: dict[str, Any],
    r10_external_evidence_registry: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_independent_data(r12_recall_mitigation_independent_holdout_data)
    _validate_external_registry(r10_external_evidence_registry)

    prioritized_sources = _prioritized_source_handoff(
        r10_external_evidence_registry["case_records"]
    )
    gates = {
        "l11_data_gap_confirmed": (
            r12_recall_mitigation_independent_holdout_data["acceptance_gates"][
                "mitigation_independent_data_ready"
            ]
            is False
        ),
        "external_candidate_sources_registered": bool(prioritized_sources),
        "ingestion_contract_ready": True,
        "customer_slice_contract_ready": True,
        "raw_external_or_customer_slice_present": False,
        "minimum_case_count_met": False,
        "customer_approval_present": False,
        "independent_holdout_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": (
            R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice_ready_contract_blocked_no_raw_slice"
        ),
        "claim_level": "ingestion_or_customer_slice_contract_only",
        "route_selection": {
            "selected_route": "external_public_holdout_first_customer_slice_compatible",
            "selection_reason": (
                "L11 found no independent dataset, no low-sensitive recall slice, "
                "and no customer-approved holdout; use registered official sources "
                "or a customer-approved slice before revalidation."
            ),
            "preferred_external_source_id": (
                "dot_air_travel_consumer_report_complaint_candidate"
            ),
            "customer_slice_fallback_enabled": True,
        },
        "prioritized_source_handoff": prioritized_sources,
        "customer_slice_contract": {
            "accepted_file_types": ["csv", "jsonl"],
            "minimum_case_count": 10,
            "required_columns": [
                "case_id",
                "scenario_family",
                "segment_column",
                "segment_value",
                "static_prior_prediction",
                "interaction_prediction",
                "observed_outcome",
                "outcome_window_start",
                "outcome_window_end",
                "customer_approval_id",
                "source_ref",
            ],
            "optional_columns": [
                "complaint_count",
                "exposure_count",
                "price_change_pct",
                "policy_change_label",
                "mechanism_tags",
                "segment_sensitivity_level",
            ],
            "must_include_low_sensitive_or_customer_approved_axis": True,
            "must_exclude_l9_derivation_band_as_proof": True,
            "manual_prompt_or_persona_patch_allowed": False,
        },
        "revalidation_contract": {
            "target_validation_artifact": "r12_recall_mitigation_external_holdout_revalidation",
            "requires_raw_slice_before_revalidation": True,
            "requires_no_l9_derivation_band_as_only_proof": True,
            "requires_false_alarm_non_regression": True,
            "requires_recall_gain_retention_or_explicit_failure": True,
            "product_default_allowed_before_revalidation": False,
        },
        "acceptance_gates": gates,
        "acceptance_decision": (
            "ready_to_ingest_external_or_customer_slice_keep_product_default_blocked"
        ),
        "next_required_artifact": "r12_external_or_customer_holdout_raw_slice",
        "source_refs": [
            r12_recall_mitigation_independent_holdout_data["artifact_id"],
            r10_external_evidence_registry["artifact_id"],
        ],
        "source_registry": [
            {
                "artifact_id": r12_recall_mitigation_independent_holdout_data[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_mitigation_independent_holdout_data/"
                    "r12-recall-mitigation-independent-holdout-data-current-001.json"
                ),
            },
            {
                "artifact_id": r10_external_evidence_registry["artifact_id"],
                "path": (
                    "experiments/results/r10_external_evidence_registry/"
                    "r10-external-evidence-registry-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "R12 now has a concrete external-or-customer holdout ingestion "
                "contract for the next validation step."
            ),
            (
                "The Product workflow can ask for official external data or a "
                "customer-approved outcome slice without enabling runtime default."
            ),
        ],
        "blocked_claims": [
            "raw external or customer holdout slice present",
            "external holdout revalidation completed",
            "customer approved holdout validation completed",
            "mitigation independent data ready",
            "R12 Product default high-risk recovery validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            **kwargs
        ),
    )


def _prioritized_source_handoff(
    case_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    priority_order = [
        (
            "dot_air_travel_consumer_report_complaint_candidate",
            "r12_dot_atcr_complaint_holdout_ingestion",
            "service_change_complaint_risk_external_holdout",
        ),
        (
            "bts_db1b_route_price_demand_candidate",
            "r12_bts_db1b_price_demand_holdout_ingestion",
            "price_change_revealed_demand_external_holdout",
        ),
        (
            "census_hps_policy_reaction_public_use_candidate",
            "r12_hps_independent_wave_holdout_ingestion",
            "policy_reaction_survey_external_holdout",
        ),
    ]
    records_by_id = {record["case_id"]: record for record in case_records}
    handoff = []
    for priority, (case_id, next_artifact, product_use) in enumerate(
        priority_order,
        start=1,
    ):
        record = records_by_id[case_id]
        handoff.append(
            {
                "priority": priority,
                "case_id": case_id,
                "domain": record["domain"],
                "ingestion_status": record["ingestion_status"],
                "target_next_artifact": next_artifact,
                "product_use": product_use,
            }
        )
    return handoff


def _validate_independent_data(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION
    ):
        raise ValueError("r12 independent holdout data schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 independent holdout data acceptance_gates required")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 independent data audit must block Product default")
    if artifact.get("next_required_artifact") != (
        "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice"
    ):
        raise ValueError("r12 independent data audit must request L12 contract")


def _validate_external_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION:
        raise ValueError("r10 external evidence registry schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r10 external evidence registry acceptance_gates required")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("external evidence registry must not allow runtime default")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-recall-mitigation-independent-holdout-data-path",
        required=True,
    )
    parser.add_argument("--r10-external-evidence-registry-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = (
        write_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
            output=args.output,
            artifact_id=args.artifact_id,
            run_id=args.run_id,
            r12_recall_mitigation_independent_holdout_data=load_json_artifact(
                args.r12_recall_mitigation_independent_holdout_data_path
            ),
            r10_external_evidence_registry=load_json_artifact(
                args.r10_external_evidence_registry_path
            ),
        )
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
