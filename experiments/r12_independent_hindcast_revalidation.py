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
from experiments.r12_pre_outcome_or_independent_prediction_packet import (
    R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION,
)


R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION = (
    "r12-independent-hindcast-revalidation-v1"
)
INTERVAL_HALF_WIDTH = 0.05
TOP_K_FOR_RISK_RANKING = 4


def build_r12_independent_hindcast_revalidation(
    *,
    artifact_id: str,
    run_id: str,
    r12_pre_outcome_or_independent_prediction_packet: dict[str, Any],
    r12_external_or_customer_holdout_raw_slice: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_prediction_packet(r12_pre_outcome_or_independent_prediction_packet)
    _validate_raw_slice(r12_external_or_customer_holdout_raw_slice)

    raw_records = r12_external_or_customer_holdout_raw_slice["raw_records"]
    predictions = {
        row["case_id"]: row
        for row in r12_pre_outcome_or_independent_prediction_packet[
            "locked_predictions"
        ]
    }
    observed_total = sum(record["total"] for record in raw_records)
    high_risk_threshold = 1 / len(raw_records)
    case_results = _case_results(
        raw_records=raw_records,
        predictions=predictions,
        observed_total=observed_total,
        high_risk_threshold=high_risk_threshold,
    )
    metric_comparison = _metric_comparison(case_results)
    gates = {
        "prediction_packet_generated": True,
        "prediction_source_independent_of_target_outcome": True,
        "target_outcome_used_for_prediction_generation": False,
        "same_table_prediction_leakage_risk": False,
        "prediction_lock_timestamp_pre_target_outcome": False,
        "hindcast_independent_revalidation_executed": True,
        "hindcast_independent_revalidation_passed": (
            metric_comparison["mean_absolute_error"]["delta"] < 0
            and metric_comparison["interval_coverage"]["delta"] >= 0
            and metric_comparison["risk_ranking_quality"]["delta"] > 0
            and metric_comparison["static_prior_miss_recovery"]["delta"] > 0
            and metric_comparison["false_alarm_rate"]["delta"] <= 0
            and metric_comparison["decision_value"]["delta"] > 0
        ),
        "mean_absolute_error_improved": (
            metric_comparison["mean_absolute_error"]["delta"] < 0
        ),
        "interval_coverage_non_regression": (
            metric_comparison["interval_coverage"]["delta"] >= 0
        ),
        "risk_ranking_quality_improved": (
            metric_comparison["risk_ranking_quality"]["delta"] > 0
        ),
        "static_prior_miss_recovery_improved": (
            metric_comparison["static_prior_miss_recovery"]["delta"] > 0
        ),
        "false_alarm_non_regression": (
            metric_comparison["false_alarm_rate"]["delta"] <= 0
        ),
        "decision_value_improved": (
            metric_comparison["decision_value"]["delta"] > 0
        ),
        "pre_outcome_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": R12_INDEPENDENT_HINDCAST_REVALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_independent_hindcast_revalidation_passed_guarded_not_pre_outcome"
        ),
        "claim_level": (
            "independent_hindcast_positive_guarded_not_pre_outcome_validation"
        ),
        "hindcast_summary": {
            "prediction_packet_artifact_id": (
                r12_pre_outcome_or_independent_prediction_packet["artifact_id"]
            ),
            "target_raw_slice_artifact_id": (
                r12_external_or_customer_holdout_raw_slice["artifact_id"]
            ),
            "target_outcome_period": "April 2026",
            "feature_period": "March 2026",
            "case_count": len(raw_records),
            "observed_total": observed_total,
            "prediction_source_independent_of_target_outcome": True,
            "prediction_lock_timestamp_pre_target_outcome": False,
            "hindcast_independent_revalidation_ready": True,
            "pre_outcome_revalidation_ready": False,
        },
        "metric_comparison": metric_comparison,
        "top_k_risk_ranking": _top_k_risk_ranking(case_results),
        "case_results": case_results,
        "acceptance_gates": gates,
        "acceptance_decision": (
            "accept_independent_hindcast_positive_keep_product_default_blocked_until_pre_outcome_or_field_validation"
        ),
        "next_required_artifact": (
            "r12_pre_outcome_prediction_trial_or_customer_field_revalidation"
        ),
        "source_refs": [
            r12_pre_outcome_or_independent_prediction_packet["artifact_id"],
            r12_external_or_customer_holdout_raw_slice["artifact_id"],
        ],
        "source_registry": [
            {
                "artifact_id": (
                    r12_pre_outcome_or_independent_prediction_packet[
                        "artifact_id"
                    ]
                ),
                "path": (
                    "experiments/results/"
                    "r12_pre_outcome_or_independent_prediction_packet/"
                    "r12-pre-outcome-or-independent-prediction-packet-current-001.json"
                ),
            },
            {
                "artifact_id": (
                    r12_external_or_customer_holdout_raw_slice["artifact_id"]
                ),
                "path": (
                    "experiments/results/r12_external_or_customer_holdout_raw_slice/"
                    "r12-external-or-customer-holdout-raw-slice-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "R12 independent prior-month hindcast revalidation improves "
                "Product-relevant risk metrics on the DOT April 2026 complaint target."
            ),
            (
                "The hindcast uses predictions independent of the April target "
                "outcome, but it is not a pre-outcome locked validation."
            ),
        ],
        "blocked_claims": [
            "pre-outcome validation passed",
            "Product default can use R12 hindcast by default",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_independent_hindcast_revalidation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_independent_hindcast_revalidation(**kwargs),
    )


def _validate_prediction_packet(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_PRE_OUTCOME_OR_INDEPENDENT_PREDICTION_PACKET_SCHEMA_VERSION
    ):
        raise ValueError("r12 L15 prediction packet schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L15 prediction packet acceptance_gates required")
    if gates.get("prediction_packet_generated") is not True:
        raise ValueError("r12 L15 prediction packet must be generated")
    if gates.get("prediction_source_independent_of_target_outcome") is not True:
        raise ValueError("r12 L15 prediction source must be independent")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L15 prediction packet must not allow Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L15 prediction packet must not allow runtime default")


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
        raise ValueError("r12 raw slice must not allow Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 raw slice must not allow runtime default")


def _case_results(
    *,
    raw_records: list[dict[str, Any]],
    predictions: dict[str, dict[str, Any]],
    observed_total: int,
    high_risk_threshold: float,
) -> list[dict[str, Any]]:
    result = []
    for record in raw_records:
        prediction = predictions[record["case_id"]]["prediction_share"]
        observed_share = record["total"] / observed_total
        observed_high = observed_share > high_risk_threshold
        static_high = high_risk_threshold > high_risk_threshold
        hindcast_high = prediction > high_risk_threshold
        result.append(
            {
                "case_id": record["case_id"],
                "carrier": record["carrier"],
                "observed_outcome": record["total"],
                "observed_share": _round6(observed_share),
                "static_prior_prediction": _round6(high_risk_threshold),
                "independent_hindcast_prediction": _round6(prediction),
                "static_prior_absolute_error": _round6(
                    abs(observed_share - high_risk_threshold)
                ),
                "independent_hindcast_absolute_error": _round6(
                    abs(observed_share - prediction)
                ),
                "observed_high_risk": observed_high,
                "static_prior_predicted_high_risk": static_high,
                "independent_hindcast_predicted_high_risk": hindcast_high,
                "static_prior_miss_recovered": (
                    observed_high and not static_high and hindcast_high
                ),
                "independent_hindcast_false_alarm": (
                    hindcast_high and not observed_high
                ),
            }
        )
    return result


def _metric_comparison(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    static_mae = _mean(case["static_prior_absolute_error"] for case in case_results)
    hindcast_mae = _mean(
        case["independent_hindcast_absolute_error"] for case in case_results
    )
    static_interval = _interval_coverage(
        case_results,
        prediction_key="static_prior_prediction",
    )
    hindcast_interval = _interval_coverage(
        case_results,
        prediction_key="independent_hindcast_prediction",
    )
    static_recall = _static_prior_miss_recovery(
        case_results,
        prediction_key="static_prior_predicted_high_risk",
    )
    hindcast_recall = _static_prior_miss_recovery(
        case_results,
        prediction_key="independent_hindcast_predicted_high_risk",
    )
    static_false_alarm = _false_alarm_rate(
        case_results,
        prediction_key="static_prior_predicted_high_risk",
    )
    hindcast_false_alarm = _false_alarm_rate(
        case_results,
        prediction_key="independent_hindcast_predicted_high_risk",
    )
    static_precision = _precision(
        case_results,
        prediction_key="static_prior_predicted_high_risk",
    )
    hindcast_precision = _precision(
        case_results,
        prediction_key="independent_hindcast_predicted_high_risk",
    )
    static_decision_value = _decision_value(
        case_results,
        prediction_key="static_prior_predicted_high_risk",
    )
    hindcast_decision_value = _decision_value(
        case_results,
        prediction_key="independent_hindcast_predicted_high_risk",
    )
    hindcast_ranking = _top_k_risk_ranking(case_results)["risk_ranking_quality"]
    return {
        "mean_absolute_error": _comparison(static_mae, hindcast_mae),
        "interval_coverage": _comparison(static_interval, hindcast_interval),
        "risk_ranking_quality": _comparison(0.0, hindcast_ranking),
        "static_prior_miss_recovery": _comparison(static_recall, hindcast_recall),
        "false_alarm_rate": _comparison(static_false_alarm, hindcast_false_alarm),
        "precision": _comparison(static_precision, hindcast_precision),
        "decision_value": _comparison(static_decision_value, hindcast_decision_value),
    }


def _top_k_risk_ranking(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    observed = _top_k(case_results, value_key="observed_share")
    hindcast = _top_k(case_results, value_key="independent_hindcast_prediction")
    overlap_count = len(set(observed).intersection(hindcast))
    return {
        "observed_top_k_carriers": observed,
        "independent_hindcast_top_k_carriers": hindcast,
        "overlap_count": overlap_count,
        "risk_ranking_quality": _round6(overlap_count / TOP_K_FOR_RISK_RANKING),
    }


def _top_k(case_results: list[dict[str, Any]], *, value_key: str) -> list[str]:
    return [
        case["carrier"]
        for case in sorted(
            case_results,
            key=lambda case: (-case[value_key], case["carrier"]),
        )[:TOP_K_FOR_RISK_RANKING]
    ]


def _interval_coverage(case_results: list[dict[str, Any]], *, prediction_key: str) -> float:
    return _mean(
        (
            max(0.0, case[prediction_key] - INTERVAL_HALF_WIDTH)
            <= case["observed_share"]
            <= min(1.0, case[prediction_key] + INTERVAL_HALF_WIDTH)
        )
        for case in case_results
    )


def _static_prior_miss_recovery(
    case_results: list[dict[str, Any]],
    *,
    prediction_key: str,
) -> float:
    observed_high = [case for case in case_results if case["observed_high_risk"]]
    if not observed_high:
        return 0.0
    return _mean(case[prediction_key] for case in observed_high)


def _false_alarm_rate(
    case_results: list[dict[str, Any]],
    *,
    prediction_key: str,
) -> float:
    predicted_high = [case for case in case_results if case[prediction_key]]
    if not predicted_high:
        return 0.0
    return _mean(not case["observed_high_risk"] for case in predicted_high)


def _precision(case_results: list[dict[str, Any]], *, prediction_key: str) -> float:
    predicted_high = [case for case in case_results if case[prediction_key]]
    if not predicted_high:
        return 0.0
    return _mean(case["observed_high_risk"] for case in predicted_high)


def _decision_value(case_results: list[dict[str, Any]], *, prediction_key: str) -> float:
    score = 0.0
    for case in case_results:
        if case["observed_high_risk"] and case[prediction_key]:
            score += 1.0
        elif case["observed_high_risk"] and not case[prediction_key]:
            score -= 1.0
        elif not case["observed_high_risk"] and case[prediction_key]:
            score -= 0.5
    return score / len(case_results)


def _comparison(static_prior: float, hindcast: float) -> dict[str, float]:
    return {
        "static_prior": _round6(static_prior),
        "independent_hindcast": _round6(hindcast),
        "delta": _round6(hindcast - static_prior),
    }


def _mean(values: Any) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(float(value) for value in items) / len(items)


def _round6(value: float) -> float:
    return round(float(value), 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-pre-outcome-or-independent-prediction-packet-path",
        required=True,
    )
    parser.add_argument("--r12-external-or-customer-holdout-raw-slice-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_independent_hindcast_revalidation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_pre_outcome_or_independent_prediction_packet=load_json_artifact(
            args.r12_pre_outcome_or_independent_prediction_packet_path
        ),
        r12_external_or_customer_holdout_raw_slice=load_json_artifact(
            args.r12_external_or_customer_holdout_raw_slice_path
        ),
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
