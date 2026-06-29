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


R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION = (
    "r12-recall-mitigation-external-holdout-revalidation-v1"
)
MECHANISM_PRESSURE_WEIGHTS = {
    "refunds": 0.30,
    "flight_problems": 0.25,
    "baggage": 0.15,
    "customer_service": 0.10,
    "denied_boarding": 0.07,
    "disability": 0.05,
    "fees_fares": 0.04,
    "reservations_ticketing_boarding": 0.03,
    "advertising": 0.005,
    "discrimination": 0.005,
}
INTERVAL_HALF_WIDTH = 0.05
TOP_K_FOR_RISK_RANKING = 4


def build_r12_recall_mitigation_external_holdout_revalidation(
    *,
    artifact_id: str,
    run_id: str,
    r12_external_or_customer_holdout_raw_slice: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_raw_slice(r12_external_or_customer_holdout_raw_slice)

    raw_records = r12_external_or_customer_holdout_raw_slice["raw_records"]
    observed_total = sum(record["total"] for record in raw_records)
    case_count = len(raw_records)
    static_prior_prediction = 1 / case_count
    pressure_scores = [_mechanism_pressure_score(record) for record in raw_records]
    score_total = sum(pressure_scores)
    interaction_predictions = [score / score_total for score in pressure_scores]
    case_predictions = _case_predictions(
        raw_records=raw_records,
        observed_total=observed_total,
        static_prior_prediction=static_prior_prediction,
        interaction_predictions=interaction_predictions,
        pressure_scores=pressure_scores,
    )
    metric_comparison = _metric_comparison(case_predictions)
    gates = {
        "raw_external_or_customer_slice_present": True,
        "prediction_fields_generated": True,
        "external_holdout_revalidation_executed": True,
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
        "prediction_source_independent_of_observed_outcome": False,
        "same_table_prediction_leakage_risk": True,
        "external_holdout_revalidation_passed": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": (
            R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_REVALIDATION_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_recall_mitigation_external_holdout_revalidation_blocked_prediction_proxy_only"
        ),
        "claim_level": "external_holdout_proxy_revalidation_diagnostic_only",
        "revalidation_summary": {
            "source_artifact_id": r12_external_or_customer_holdout_raw_slice[
                "artifact_id"
            ],
            "case_count": case_count,
            "observed_total": observed_total,
            "high_risk_threshold": _round6(static_prior_prediction),
            "top_k_for_risk_ranking": TOP_K_FOR_RISK_RANKING,
            "static_prior_prediction_source": "uniform_carrier_share_control",
            "interaction_prediction_source": (
                "same_table_mechanism_composition_proxy"
            ),
            "prediction_source_independent_of_observed_outcome": False,
            "same_table_prediction_leakage_risk": True,
        },
        "metric_comparison": metric_comparison,
        "top_k_risk_ranking": _top_k_risk_ranking(case_predictions),
        "case_predictions": case_predictions,
        "acceptance_gates": gates,
        "acceptance_decision": (
            "reject_product_default_keep_as_proxy_external_revalidation_diagnostic"
        ),
        "next_required_artifact": "r12_pre_outcome_or_independent_prediction_packet",
        "source_refs": [
            r12_external_or_customer_holdout_raw_slice["artifact_id"],
            "dot_air_travel_consumer_report_complaint_candidate",
        ],
        "source_registry": [
            {
                "artifact_id": r12_external_or_customer_holdout_raw_slice[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_external_or_customer_holdout_raw_slice/"
                    "r12-external-or-customer-holdout-raw-slice-current-001.json"
                ),
            }
        ],
        "allowed_claims": [
            (
                "R12 can compute proxy external holdout revalidation metrics on "
                "the DOT ATCR raw slice."
            ),
            (
                "The proxy interaction signal improves recall-oriented metrics "
                "but increases false alarms and is not an independent prediction."
            ),
        ],
        "blocked_claims": [
            "external holdout revalidation passed with independent predictions",
            "prediction source independent of observed outcome",
            "false_alarm_non_regression=true",
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


def write_r12_recall_mitigation_external_holdout_revalidation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_recall_mitigation_external_holdout_revalidation(**kwargs),
    )


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
    raw_records = artifact.get("raw_records")
    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("r12 raw slice raw_records required")
    if sum(record["total"] for record in raw_records) <= 0:
        raise ValueError("r12 raw slice observed total must be positive")


def _mechanism_pressure_score(record: dict[str, Any]) -> float:
    total = record["total"]
    return sum(
        (record[key] / total) * weight
        for key, weight in MECHANISM_PRESSURE_WEIGHTS.items()
    )


def _case_predictions(
    *,
    raw_records: list[dict[str, Any]],
    observed_total: int,
    static_prior_prediction: float,
    interaction_predictions: list[float],
    pressure_scores: list[float],
) -> list[dict[str, Any]]:
    result = []
    high_risk_threshold = static_prior_prediction
    for record, interaction_prediction, pressure_score in zip(
        raw_records,
        interaction_predictions,
        pressure_scores,
        strict=True,
    ):
        observed_share = record["total"] / observed_total
        observed_high = observed_share > high_risk_threshold
        static_high = static_prior_prediction > high_risk_threshold
        interaction_high = interaction_prediction > high_risk_threshold
        result.append(
            {
                "case_id": record["case_id"],
                "carrier": record["carrier"],
                "observed_outcome": record["total"],
                "observed_share": _round6(observed_share),
                "static_prior_prediction": _round6(static_prior_prediction),
                "interaction_prediction": _round6(interaction_prediction),
                "mechanism_pressure_score": _round6(pressure_score),
                "static_prior_absolute_error": _round6(
                    abs(observed_share - static_prior_prediction)
                ),
                "interaction_absolute_error": _round6(
                    abs(observed_share - interaction_prediction)
                ),
                "observed_high_risk": observed_high,
                "static_prior_predicted_high_risk": static_high,
                "interaction_predicted_high_risk": interaction_high,
                "static_prior_miss_recovered": (
                    observed_high and not static_high and interaction_high
                ),
                "interaction_false_alarm": (
                    interaction_high and not observed_high
                ),
            }
        )
    return result


def _metric_comparison(case_predictions: list[dict[str, Any]]) -> dict[str, Any]:
    static_mae = _mean(
        case["static_prior_absolute_error"] for case in case_predictions
    )
    interaction_mae = _mean(
        case["interaction_absolute_error"] for case in case_predictions
    )
    static_interval_coverage = _interval_coverage(
        case_predictions,
        prediction_key="static_prior_prediction",
    )
    interaction_interval_coverage = _interval_coverage(
        case_predictions,
        prediction_key="interaction_prediction",
    )
    static_miss_recovery = _static_prior_miss_recovery(
        case_predictions,
        prediction_key="static_prior_predicted_high_risk",
    )
    interaction_miss_recovery = _static_prior_miss_recovery(
        case_predictions,
        prediction_key="interaction_predicted_high_risk",
    )
    static_false_alarm_rate = _false_alarm_rate(
        case_predictions,
        prediction_key="static_prior_predicted_high_risk",
    )
    interaction_false_alarm_rate = _false_alarm_rate(
        case_predictions,
        prediction_key="interaction_predicted_high_risk",
    )
    static_precision = _precision(
        case_predictions,
        prediction_key="static_prior_predicted_high_risk",
    )
    interaction_precision = _precision(
        case_predictions,
        prediction_key="interaction_predicted_high_risk",
    )
    interaction_ranking = _top_k_risk_ranking(case_predictions)[
        "risk_ranking_quality"
    ]
    return {
        "mean_absolute_error": _comparison(static_mae, interaction_mae),
        "interval_coverage": _comparison(
            static_interval_coverage,
            interaction_interval_coverage,
        ),
        "risk_ranking_quality": _comparison(0.0, interaction_ranking),
        "static_prior_miss_recovery": _comparison(
            static_miss_recovery,
            interaction_miss_recovery,
        ),
        "false_alarm_rate": _comparison(
            static_false_alarm_rate,
            interaction_false_alarm_rate,
        ),
        "precision": _comparison(static_precision, interaction_precision),
    }


def _top_k_risk_ranking(case_predictions: list[dict[str, Any]]) -> dict[str, Any]:
    observed = _top_k(
        case_predictions,
        value_key="observed_share",
    )
    interaction = _top_k(
        case_predictions,
        value_key="interaction_prediction",
    )
    overlap_count = len(set(observed).intersection(interaction))
    return {
        "observed_top_k_carriers": observed,
        "interaction_top_k_carriers": interaction,
        "overlap_count": overlap_count,
        "risk_ranking_quality": _round6(overlap_count / TOP_K_FOR_RISK_RANKING),
    }


def _top_k(case_predictions: list[dict[str, Any]], *, value_key: str) -> list[str]:
    return [
        case["carrier"]
        for case in sorted(
            case_predictions,
            key=lambda case: (-case[value_key], case["carrier"]),
        )[:TOP_K_FOR_RISK_RANKING]
    ]


def _interval_coverage(
    case_predictions: list[dict[str, Any]],
    *,
    prediction_key: str,
) -> float:
    return _mean(
        (
            max(0.0, case[prediction_key] - INTERVAL_HALF_WIDTH)
            <= case["observed_share"]
            <= min(1.0, case[prediction_key] + INTERVAL_HALF_WIDTH)
        )
        for case in case_predictions
    )


def _static_prior_miss_recovery(
    case_predictions: list[dict[str, Any]],
    *,
    prediction_key: str,
) -> float:
    observed_high = [
        case for case in case_predictions if case["observed_high_risk"]
    ]
    if not observed_high:
        return 0.0
    return _mean(case[prediction_key] for case in observed_high)


def _false_alarm_rate(
    case_predictions: list[dict[str, Any]],
    *,
    prediction_key: str,
) -> float:
    predicted_high = [case for case in case_predictions if case[prediction_key]]
    if not predicted_high:
        return 0.0
    return _mean(not case["observed_high_risk"] for case in predicted_high)


def _precision(
    case_predictions: list[dict[str, Any]],
    *,
    prediction_key: str,
) -> float:
    predicted_high = [case for case in case_predictions if case[prediction_key]]
    if not predicted_high:
        return 0.0
    return _mean(case["observed_high_risk"] for case in predicted_high)


def _comparison(static_prior: float, interaction: float) -> dict[str, float]:
    return {
        "static_prior": _round6(static_prior),
        "interaction": _round6(interaction),
        "delta": _round6(interaction - static_prior),
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
    parser.add_argument("--r12-external-or-customer-holdout-raw-slice-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_recall_mitigation_external_holdout_revalidation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
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
