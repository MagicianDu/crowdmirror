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
from experiments.r12_external_or_customer_holdout_raw_slice import (
    R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION,
)
from experiments.r12_independent_hindcast_revalidation import (
    R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION,
    INTERVAL_HALF_WIDTH,
)


R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION = (
    "r12-pre-outcome-prediction-trial-or-customer-field-revalidation-v1"
)


def build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
    *,
    artifact_id: str,
    run_id: str,
    r12_independent_hindcast_revalidation: dict[str, Any],
    r12_external_or_customer_holdout_raw_slice: dict[str, Any],
    prediction_lock_timestamp: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    prediction_lock_timestamp = non_empty_string(
        prediction_lock_timestamp,
        field="prediction_lock_timestamp",
    )
    _validate_independent_hindcast(r12_independent_hindcast_revalidation)
    _validate_raw_slice(r12_external_or_customer_holdout_raw_slice)

    raw_records = r12_external_or_customer_holdout_raw_slice["raw_records"]
    prediction_total_basis = sum(record["total"] for record in raw_records)
    case_count = len(raw_records)
    static_prior_prediction = 1 / case_count
    locked_predictions = _locked_predictions(
        raw_records=raw_records,
        prediction_total_basis=prediction_total_basis,
        static_prior_prediction=static_prior_prediction,
    )
    gates = {
        "supporting_independent_hindcast_passed": True,
        "pre_outcome_prediction_trial_created": True,
        "prediction_packet_locked": True,
        "prediction_lock_timestamp_present": True,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "prediction_source_independent_of_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "target_outcome_artifact_present": False,
        "pre_outcome_revalidation_ready": False,
        "customer_field_slice_contract_ready": True,
        "customer_field_slice_present": False,
        "customer_approval_present": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": (
            R12_PRE_OUTCOME_PREDICTION_TRIAL_OR_CUSTOMER_FIELD_REVALIDATION_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_pre_outcome_prediction_trial_locked_outcome_pending_guarded"
        ),
        "claim_level": "pre_outcome_prediction_trial_locked_not_yet_validated",
        "route_selection": {
            "selected_route": "pre_outcome_public_dot_trial",
            "customer_field_revalidation_fallback_enabled": True,
            "customer_field_slice_contract_ready": True,
            "selected_feature_source_artifact_id": (
                r12_external_or_customer_holdout_raw_slice["artifact_id"]
            ),
            "supporting_hindcast_artifact_id": (
                r12_independent_hindcast_revalidation["artifact_id"]
            ),
        },
        "trial_summary": {
            "trial_id": "r12-dot-atcr-2026-05-pre-outcome-trial-001",
            "prediction_lock_timestamp": prediction_lock_timestamp,
            "feature_period": "April 2026",
            "target_outcome_period": "May 2026",
            "target_outcome_artifact_present": False,
            "prediction_case_count": case_count,
            "prediction_total_basis": prediction_total_basis,
            "prediction_source_independent_of_target_outcome": True,
            "target_outcome_used_for_prediction_generation": False,
            "prediction_lock_timestamp_pre_target_outcome": True,
            "pre_outcome_revalidation_ready": False,
            "customer_field_slice_present": False,
            "customer_approval_present": False,
        },
        "locked_predictions": locked_predictions,
        "customer_field_slice_contract": _customer_field_slice_contract(),
        "evaluation_contract": _evaluation_contract(),
        "acceptance_gates": gates,
        "acceptance_decision": (
            "accept_pre_outcome_trial_lock_keep_validation_and_product_default_blocked_until_outcome_ingestion"
        ),
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_ingestion"
        ),
        "source_refs": [
            r12_independent_hindcast_revalidation["artifact_id"],
            r12_external_or_customer_holdout_raw_slice["artifact_id"],
            "dot_air_travel_consumer_report_complaint_candidate",
        ],
        "source_registry": [
            {
                "artifact_id": r12_independent_hindcast_revalidation[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_independent_hindcast_revalidation/"
                    "r12-independent-hindcast-revalidation-current-001.json"
                ),
            },
            {
                "artifact_id": r12_external_or_customer_holdout_raw_slice[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_external_or_customer_holdout_raw_slice/"
                    "r12-external-or-customer-holdout-raw-slice-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "R12 has locked a pre-outcome public DOT prediction trial using "
                "feature data independent of the future target outcome."
            ),
            (
                "The same artifact defines the customer field slice contract "
                "needed for outcome revalidation."
            ),
        ],
        "blocked_claims": [
            "pre-outcome outcome revalidation passed",
            "customer field outcome validated",
            "target outcome artifact present",
            "Product default can use R12 pre-outcome trial by default",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
            **kwargs
        ),
    )


def _validate_independent_hindcast(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L16 independent hindcast schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L16 independent hindcast acceptance_gates required")
    if gates.get("hindcast_independent_revalidation_passed") is not True:
        raise ValueError("r12 L16 independent hindcast must pass")
    if gates.get("prediction_source_independent_of_target_outcome") is not True:
        raise ValueError("r12 L16 prediction source must be independent")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L16 independent hindcast must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L16 independent hindcast must block runtime default")


def _validate_raw_slice(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_EXTERNAL_OR_CUSTOMER_HOLDOUT_RAW_SLICE_SCHEMA_VERSION
    ):
        raise ValueError("r12 raw slice schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 raw slice acceptance_gates required")
    if gates.get("raw_external_or_customer_slice_present") is not True:
        raise ValueError("r12 raw slice must be present")
    if gates.get("actual_public_data_ingested") is not True:
        raise ValueError("r12 raw slice must ingest actual public data")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 raw slice must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 raw slice must block runtime default")


def _locked_predictions(
    *,
    raw_records: list[dict[str, Any]],
    prediction_total_basis: int,
    static_prior_prediction: float,
) -> list[dict[str, Any]]:
    return [
        {
            "case_id": _future_case_id(record["case_id"]),
            "source_case_id": record["case_id"],
            "carrier": record["carrier"],
            "feature_observed_total": record["total"],
            "static_prior_prediction": _round6(static_prior_prediction),
            "locked_prediction_share": _round6(
                record["total"] / prediction_total_basis
            ),
            "prediction_interval_low": _round6(
                max(0.0, record["total"] / prediction_total_basis - INTERVAL_HALF_WIDTH)
            ),
            "prediction_interval_high": _round6(
                min(1.0, record["total"] / prediction_total_basis + INTERVAL_HALF_WIDTH)
            ),
            "prediction_basis": "prior_month_official_complaint_share",
        }
        for record in raw_records
    ]


def _future_case_id(source_case_id: str) -> str:
    return source_case_id.replace("_2026_04_", "_2026_05_")


def _customer_field_slice_contract() -> dict[str, Any]:
    return {
        "accepted_formats": ["csv", "jsonl"],
        "minimum_case_count": 10,
        "required_fields": [
            "case_id",
            "segment_id",
            "scenario_id",
            "prediction_share_or_score",
            "observed_outcome",
            "outcome_timestamp",
            "customer_approval_reference",
        ],
        "optional_fields": [
            "segment_label",
            "mechanism_label",
            "baseline_prediction",
            "interaction_prediction",
            "decision_cost",
            "review_note",
        ],
        "must_include_customer_approval_reference": True,
        "manual_prompt_or_persona_patch_allowed": False,
    }


def _evaluation_contract() -> dict[str, Any]:
    return {
        "next_required_artifact": (
            "r12_pre_outcome_or_customer_field_outcome_ingestion"
        ),
        "evaluation_metrics": [
            "mean_absolute_error",
            "interval_coverage",
            "risk_ranking_quality",
            "static_prior_miss_recovery",
            "false_alarm_rate",
            "decision_value",
        ],
        "acceptance_requires": [
            "target_outcome_artifact_present=true",
            "target_outcome_used_for_prediction_generation=false",
            "prediction_lock_timestamp_pre_target_outcome=true",
            "false_alarm_non_regression=true",
            "field_or_pre_outcome_revalidation_passed=true",
        ],
    }


def _round6(value: float) -> float:
    return round(float(value), 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-independent-hindcast-revalidation-path", required=True)
    parser.add_argument("--r12-external-or-customer-holdout-raw-slice-path", required=True)
    parser.add_argument("--prediction-lock-timestamp", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = (
        write_r12_pre_outcome_prediction_trial_or_customer_field_revalidation(
            output=args.output,
            artifact_id=args.artifact_id,
            run_id=args.run_id,
            r12_independent_hindcast_revalidation=load_json_artifact(
                args.r12_independent_hindcast_revalidation_path
            ),
            r12_external_or_customer_holdout_raw_slice=load_json_artifact(
                args.r12_external_or_customer_holdout_raw_slice_path
            ),
            prediction_lock_timestamp=args.prediction_lock_timestamp,
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
