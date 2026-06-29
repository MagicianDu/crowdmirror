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
from experiments.r12_pre_outcome_or_customer_field_outcome_ingestion import (
    R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION,
)


R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION = (
    "r12-pre-outcome-or-customer-field-outcome-revalidation-v1"
)


def build_r12_pre_outcome_or_customer_field_outcome_revalidation(
    *,
    artifact_id: str,
    run_id: str,
    r12_pre_outcome_or_customer_field_outcome_ingestion: dict[str, Any],
    revalidation_requested_at: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    revalidation_requested_at = non_empty_string(
        revalidation_requested_at,
        field="revalidation_requested_at",
    )
    _validate_l18_ingestion(r12_pre_outcome_or_customer_field_outcome_ingestion)

    ingestion = r12_pre_outcome_or_customer_field_outcome_ingestion
    summary = ingestion["ingestion_summary"]
    gates = {
        "pre_outcome_trial_locked": True,
        "prediction_lock_timestamp_pre_target_outcome": True,
        "target_outcome_artifact_present": False,
        "customer_field_slice_present": False,
        "field_or_pre_outcome_revalidation_ready": False,
        "metrics_computed": False,
        "field_or_pre_outcome_revalidation_passed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": (
            R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_REVALIDATION_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_pre_outcome_or_customer_field_outcome_revalidation_blocked_no_outcome"
        ),
        "claim_level": "revalidation_harness_ready_no_outcome",
        "revalidation_summary": {
            "ingestion_artifact_id": ingestion["artifact_id"],
            "trial_artifact_id": summary["trial_artifact_id"],
            "target_outcome_period": summary["target_outcome_period"],
            "prediction_case_count": summary["prediction_case_count"],
            "prediction_lock_timestamp": summary["prediction_lock_timestamp"],
            "revalidation_requested_at": revalidation_requested_at,
            "target_outcome_artifact_present": False,
            "customer_field_slice_present": False,
            "field_or_pre_outcome_revalidation_ready": False,
            "metrics_computed": False,
        },
        "metric_execution_plan": _metric_execution_plan(),
        "blocked_revalidation_reason": {
            "reason": "target_outcome_or_customer_field_slice_missing",
            "missing_inputs": [
                "May 2026 DOT ATCR target outcome artifact",
                "customer-approved field outcome slice",
            ],
            "fail_closed_policy": (
                "Do not compute validation metrics and do not unlock Product "
                "or runtime defaults until at least one approved outcome source "
                "is present."
            ),
        },
        "acceptance_gates": gates,
        "acceptance_decision": (
            "reject_revalidation_without_outcome_keep_product_default_blocked"
        ),
        "next_required_artifact": (
            "r12_target_outcome_or_customer_field_slice_arrival"
        ),
        "source_refs": [
            ingestion["artifact_id"],
            "dot_air_travel_consumer_reports_index_current",
            "dot_airconsumer_latest_news_current",
        ],
        "source_registry": [
            {
                "artifact_id": ingestion["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_or_customer_field_outcome_ingestion/"
                    "r12-pre-outcome-or-customer-field-outcome-ingestion-current-001.json"
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
                "R12 has a fail-closed revalidation harness ready for future "
                "target outcome or customer field outcome arrival."
            ),
            (
                "No validation metric is computed until an approved outcome "
                "source is present."
            ),
        ],
        "blocked_claims": [
            "metrics_computed=true",
            "field_or_pre_outcome_revalidation_passed=true",
            "target outcome artifact present",
            "customer field outcome validated",
            "field_outcome_validated=true",
            "Product default can use R12 outcome revalidation by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_pre_outcome_or_customer_field_outcome_revalidation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_pre_outcome_or_customer_field_outcome_revalidation(**kwargs),
    )


def _validate_l18_ingestion(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_OR_CUSTOMER_FIELD_OUTCOME_INGESTION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L18 outcome ingestion schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L18 outcome ingestion acceptance_gates required")
    if gates.get("pre_outcome_trial_locked") is not True:
        raise ValueError("r12 L18 outcome ingestion requires locked trial")
    if gates.get("prediction_lock_timestamp_pre_target_outcome") is not True:
        raise ValueError("r12 L18 prediction lock must be pre-target")
    if gates.get("target_outcome_artifact_present") is not False:
        raise ValueError("r12 L18 must not contain target outcome yet")
    if gates.get("customer_field_slice_present") is not False:
        raise ValueError("r12 L18 must not contain customer field slice yet")
    if gates.get("field_or_pre_outcome_revalidation_ready") is not False:
        raise ValueError("r12 L18 must not be revalidation-ready yet")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 L18 must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L18 must block runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L18 must block Product default")


def _metric_execution_plan() -> list[dict[str, Any]]:
    return [
        {
            "metric": "mean_absolute_error",
            "required_inputs": [
                "locked_prediction_share_or_score",
                "observed_outcome",
            ],
            "acceptance_threshold": "mechanism_update_mae <= static_prior_mae",
        },
        {
            "metric": "interval_coverage",
            "required_inputs": [
                "locked_prediction_interval",
                "observed_outcome",
            ],
            "acceptance_threshold": "coverage >= static_prior_coverage",
        },
        {
            "metric": "risk_ranking_quality",
            "required_inputs": [
                "locked_risk_rank",
                "observed_outcome_rank",
            ],
            "acceptance_threshold": (
                "ranking_quality >= static_prior_ranking_quality"
            ),
        },
        {
            "metric": "static_prior_miss_recovery",
            "required_inputs": [
                "static_prior_prediction",
                "mechanism_update_prediction",
                "observed_outcome",
            ],
            "acceptance_threshold": "recovery_count > 0",
        },
        {
            "metric": "false_alarm_rate",
            "required_inputs": [
                "locked_risk_alert",
                "observed_outcome",
            ],
            "acceptance_threshold": (
                "false_alarm_rate <= static_prior_false_alarm_rate"
            ),
        },
        {
            "metric": "decision_value",
            "required_inputs": [
                "locked_decision_action",
                "observed_outcome",
                "decision_cost_model",
            ],
            "acceptance_threshold": (
                "decision_value >= static_prior_decision_value"
            ),
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-pre-outcome-or-customer-field-outcome-ingestion-path",
        required=True,
    )
    parser.add_argument("--revalidation-requested-at", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_pre_outcome_or_customer_field_outcome_revalidation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_pre_outcome_or_customer_field_outcome_ingestion=load_json_artifact(
            args.r12_pre_outcome_or_customer_field_outcome_ingestion_path
        ),
        revalidation_requested_at=args.revalidation_requested_at,
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
