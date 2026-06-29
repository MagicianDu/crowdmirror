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
from experiments.r12_pre_outcome_prediction_trial_or_customer_field_revalidation import (
    R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION,
)


R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION = (
    "r12-pre-outcome-or-customer-field-outcome-ingestion-v1"
)


def build_r12_pre_outcome_or_customer_field_outcome_ingestion(
    *,
    artifact_id: str,
    run_id: str,
    r12_pre_outcome_prediction_trial_or_customer_field_revalidation: dict[
        str, Any
    ],
    availability_checked_at: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    availability_checked_at = non_empty_string(
        availability_checked_at,
        field="availability_checked_at",
    )
    _validate_l17_trial(
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation
    )

    trial = r12_pre_outcome_prediction_trial_or_customer_field_revalidation
    trial_summary = trial["trial_summary"]
    customer_contract = trial["customer_field_slice_contract"]
    gates = {
        "pre_outcome_trial_locked": True,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "target_public_outcome_available": False,
        "target_outcome_artifact_present": False,
        "customer_field_slice_contract_ready": True,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": (
            R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_pre_outcome_or_customer_field_outcome_ingestion_pending_no_target_outcome"
        ),
        "claim_level": (
            "target_outcome_ingestion_pending_customer_field_contract_ready"
        ),
        "ingestion_summary": {
            "trial_artifact_id": trial["artifact_id"],
            "trial_id": trial_summary["trial_id"],
            "feature_period": trial_summary["feature_period"],
            "target_outcome_period": trial_summary["target_outcome_period"],
            "prediction_case_count": trial_summary["prediction_case_count"],
            "prediction_lock_timestamp": trial_summary[
                "prediction_lock_timestamp"
            ],
            "availability_checked_at": availability_checked_at,
            "target_outcome_artifact_present": False,
            "customer_field_slice_present": False,
            "customer_approval_present": False,
        },
        "public_source_availability": _public_source_availability(),
        "customer_field_ingestion_contract": {
            "contract_ready": True,
            "accepted_formats": customer_contract["accepted_formats"],
            "minimum_case_count": customer_contract["minimum_case_count"],
            "required_fields": customer_contract["required_fields"],
            "customer_slice_path_provided": False,
            "manual_prompt_or_persona_patch_allowed": (
                customer_contract["manual_prompt_or_persona_patch_allowed"]
            ),
        },
        "evaluation_readiness": {
            "field_or_pre_outcome_revalidation_ready": False,
            "missing_inputs": [
                "May 2026 DOT ATCR target outcome artifact",
                "customer-approved field outcome slice",
            ],
            "next_required_artifact": (
                "r12_pre_outcome_or_customer_field_outcome_revalidation"
            ),
            "metrics_to_compute_when_available": [
                "mean_absolute_error",
                "interval_coverage",
                "risk_ranking_quality",
                "static_prior_miss_recovery",
                "false_alarm_rate",
                "decision_value",
            ],
        },
        "acceptance_gates": gates,
        "acceptance_decision": (
            "accept_outcome_ingestion_pending_keep_validation_and_product_default_blocked"
        ),
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_revalidation"
        ),
        "source_refs": [
            trial["artifact_id"],
            "dot_air_travel_consumer_reports_index_current",
            "dot_airconsumer_latest_news_current",
        ],
        "source_registry": [
            {
                "artifact_id": trial["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_prediction_trial_or_customer_field_revalidation/"
                    "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-current-001.json"
                ),
            },
            {
                "artifact_id": "dot_air_travel_consumer_reports_index_current",
                "path": (
                    "https://www.transportation.gov/individuals/"
                    "aviation-consumer-protection/air-travel-consumer-reports"
                ),
            },
            {
                "artifact_id": "dot_airconsumer_latest_news_current",
                "path": "https://www.transportation.gov/airconsumer/latest-news",
            },
        ],
        "allowed_claims": [
            (
                "R12 pre-outcome trial is locked and ready for future outcome "
                "ingestion."
            ),
            (
                "Customer-approved field slices can be ingested once supplied "
                "under the L17 contract."
            ),
        ],
        "blocked_claims": [
            "target outcome artifact present",
            "pre-outcome outcome revalidation passed",
            "customer field outcome validated",
            "field_or_pre_outcome_revalidation_ready=true",
            "Product default can use R12 outcome ingestion by default",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_pre_outcome_or_customer_field_outcome_ingestion(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_pre_outcome_or_customer_field_outcome_ingestion(**kwargs),
    )


def _validate_l17_trial(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L17 pre-outcome trial schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L17 pre-outcome trial acceptance_gates required")
    if gates.get("pre_outcome_prediction_trial_created") is not True:
        raise ValueError("r12 L17 pre-outcome trial must be created")
    if gates.get("prediction_packet_locked") is not True:
        raise ValueError("r12 L17 prediction packet must be locked")
    if gates.get("prediction_lock_timestamp_pre_target_outcome") is not True:
        raise ValueError("r12 L17 lock must be pre-target")
    if gates.get("target_outcome_used_for_prediction_generation") is not False:
        raise ValueError("r12 L17 must not use target outcome for prediction")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L17 must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L17 must block runtime default")


def _public_source_availability() -> dict[str, Any]:
    return {
        "target_public_source_id": "dot_atcr_2026_05_target_outcome_candidate",
        "expected_public_report": (
            "July 2026 Air Travel Consumer Report (May 2026 Data)"
        ),
        "official_reports_index_url": (
            "https://www.transportation.gov/individuals/aviation-consumer-protection/air-travel-consumer-reports"
        ),
        "latest_news_url": "https://www.transportation.gov/airconsumer/latest-news",
        "latest_available_report": (
            "June 2026 Air Travel Consumer Report (April 2026 Data)"
        ),
        "target_report_found": False,
        "target_pdf_url": None,
        "target_table_available": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-pre-outcome-prediction-trial-or-customer-field-revalidation-path",
        required=True,
    )
    parser.add_argument("--availability-checked-at", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_pre_outcome_or_customer_field_outcome_ingestion(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_pre_outcome_prediction_trial_or_customer_field_revalidation=(
            load_json_artifact(
                args.r12_pre_outcome_prediction_trial_or_customer_field_revalidation_path
            )
        ),
        availability_checked_at=args.availability_checked_at,
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
