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
from experiments.r10_hps_policy_reaction_ingestion import (
    R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION,
)
from experiments.r11_interaction_risk_discoverer import (
    R11_INTERACTION_RISK_DISCOVERER_SCHEMA_VERSION,
)


R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION = (
    "r11-external-holdout-validation-v1"
)
R11_EXTERNAL_HOLDOUT_CLAIM_BOUNDARY = (
    "R11 external holdout validation artifact. It maps the R11 learnable "
    "interaction risk discoverer onto a source-backed public-use HPS proxy "
    "holdout by using PRICECONCERN as the external signal and PRICESTRESS as "
    "the held-out outcome proxy. It is not customer field validation and does "
    "not authorize Product runtime default."
)
DEFAULT_SEGMENT_COLUMNS = ["REGION", "METRO_STATUS"]
SOURCE_SIGNAL = "PRICECONCERN"
HOLDOUT_OUTCOME = "PRICESTRESS"
TREND_EPSILON = 0.015
HIGH_RISK_MARGIN = 0.03
INTERVAL_HALF_WIDTH = 0.10
EXTERNAL_HOLDOUT_FLOORS = {
    "trend_direction_accuracy": 0.333,
    "interval_coverage": 0.667,
    "risk_ranking_quality": 0.75,
    "false_alarm_rate": 0.333,
    "static_prior_miss_recovery_rate": 1.0,
    "abnormal_segment_recall": 0.667,
}


def build_r11_external_holdout_validation(
    *,
    artifact_id: str,
    run_id: str,
    r11_interaction_risk_discoverer: dict[str, Any],
    hps_ingestion: dict[str, Any],
    segment_columns: list[str] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_r11(r11_interaction_risk_discoverer)
    _validate_hps(hps_ingestion)
    segments = segment_columns or DEFAULT_SEGMENT_COLUMNS
    operator = _operator_transfer_summary(r11_interaction_risk_discoverer)
    holdout_cases = _holdout_cases(
        hps_ingestion=hps_ingestion,
        operator_transfer=operator,
        segment_columns=segments,
    )
    metrics = {
        "static_prior_external_holdout": _static_prior_metrics(holdout_cases),
        "r11_external_holdout_transfer": _r11_metrics(holdout_cases),
    }
    failure_reasons = _failure_reasons(metrics["r11_external_holdout_transfer"])
    passed = not failure_reasons
    report = {
        "schema_version": R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r11_external_holdout_validation_passed_guarded"
            if passed
            else "r11_external_holdout_validation_blocked"
        ),
        "claim_level": "public_use_proxy_holdout_only",
        "claim_boundary": R11_EXTERNAL_HOLDOUT_CLAIM_BOUNDARY,
        "validation_contract": {
            "source_backed_public_use_proxy": True,
            "source_signal": SOURCE_SIGNAL,
            "holdout_outcome_proxy": HOLDOUT_OUTCOME,
            "independent_slice_or_proxy": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "operator_transfer_summary": operator,
        "external_holdout_summary": _external_holdout_summary(
            holdout_cases=holdout_cases,
            segment_columns=segments,
        ),
        "external_holdout_cases": holdout_cases,
        "method_metrics": metrics,
        "metric_floors": EXTERNAL_HOLDOUT_FLOORS,
        "failure_reasons": failure_reasons,
        "stop_loss_or_next_step": (
            "continue_to_product_shadow_trial_guarded"
            if passed
            else "do_not_escalate_r11_until_external_holdout_failures_are_resolved"
        ),
        "acceptance_gates": {
            "external_public_use_holdout_present": bool(holdout_cases),
            "source_signal_and_holdout_proxy_distinct": SOURCE_SIGNAL != HOLDOUT_OUTCOME,
            "minimum_holdout_cases_present": len(holdout_cases) >= 3,
            "external_holdout_passed_guarded": passed,
            "product_core_method_ready": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            r11_interaction_risk_discoverer["artifact_id"],
            hps_ingestion["artifact_id"],
        ],
        "allowed_claims": [
            (
                "R11 can be audited against a source-backed public-use proxy "
                "holdout using distinct HPS signal and outcome columns."
            ),
            (
                "A passed guarded holdout may justify Product shadow-trial work, "
                "not Product runtime default."
            ),
        ],
        "blocked_claims": [
            "R11 validated",
            "R11 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "HPS proxy equals customer field outcome",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r11_external_holdout_validation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r11_external_holdout_validation(**kwargs),
    )


def _validate_r11(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R11_INTERACTION_RISK_DISCOVERER_SCHEMA_VERSION:
        raise ValueError(
            "r11_interaction_risk_discoverer.schema_version must be "
            f"{R11_INTERACTION_RISK_DISCOVERER_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r11_interaction_risk_discoverer.acceptance_gates must be an object")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r11_interaction_risk_discoverer must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r11_interaction_risk_discoverer must not allow runtime default")


def _validate_hps(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION:
        raise ValueError(
            "hps_ingestion.schema_version must be "
            f"{R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION}"
        )
    contract = artifact.get("ingestion_contract")
    if not isinstance(contract, dict):
        raise ValueError("hps_ingestion.ingestion_contract must be an object")
    if contract.get("actual_public_data_ingested") is not True:
        raise ValueError("hps_ingestion must ingest actual public data")
    if contract.get("field_outcome_validated") is not False:
        raise ValueError("hps_ingestion must not be field validated")
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError("hps_ingestion must not allow runtime default")


def _operator_transfer_summary(r11: dict[str, Any]) -> dict[str, Any]:
    operator = r11["learned_interaction_operator"]
    mechanism_weights = operator["mechanism_weights"]
    return {
        "source_operator_id": operator["operator_id"],
        "transfer_rule": (
            "apply learned price_pressure weight to segment-level PRICECONCERN "
            "deviation from the HPS global PRICECONCERN risk share"
        ),
        "transferred_mechanism": "price_pressure",
        "transferred_weight": mechanism_weights["price_pressure"],
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _holdout_cases(
    *,
    hps_ingestion: dict[str, Any],
    operator_transfer: dict[str, Any],
    segment_columns: list[str],
) -> list[dict[str, Any]]:
    global_signal = _global_risk_share(hps_ingestion, SOURCE_SIGNAL)
    global_outcome = _global_risk_share(hps_ingestion, HOLDOUT_OUTCOME)
    high_risk_threshold = round(global_outcome + HIGH_RISK_MARGIN, 6)
    source_profiles = hps_ingestion["segment_outcome_profiles"][SOURCE_SIGNAL]
    outcome_profiles = hps_ingestion["segment_outcome_profiles"][HOLDOUT_OUTCOME]
    rows = []
    for segment_column in segment_columns:
        source_by_value = {
            row["segment_value"]: row
            for row in source_profiles.get(segment_column, [])
        }
        outcome_by_value = {
            row["segment_value"]: row
            for row in outcome_profiles.get(segment_column, [])
        }
        for segment_value in sorted(set(source_by_value).intersection(outcome_by_value)):
            source_share = float(source_by_value[segment_value]["risk_proxy_share"])
            outcome_share = float(outcome_by_value[segment_value]["risk_proxy_share"])
            source_delta = source_share - global_signal
            prediction = round(
                _clip(
                    global_outcome
                    + source_delta * operator_transfer["transferred_weight"],
                    0.0,
                    1.0,
                ),
                6,
            )
            interval = _risk_interval(prediction)
            observed_high = outcome_share >= high_risk_threshold
            predicted_high = prediction >= high_risk_threshold
            static_miss = observed_high and global_outcome < high_risk_threshold
            rows.append(
                {
                    "case_id": f"hps_{segment_column}_{segment_value}",
                    "segment_column": segment_column,
                    "segment_value": segment_value,
                    "static_prior_prediction": round(global_outcome, 6),
                    "source_signal_risk_share": round(source_share, 6),
                    "source_signal_delta": round(source_delta, 6),
                    "r11_prediction": prediction,
                    "holdout_outcome_proxy": round(outcome_share, 6),
                    "high_risk_threshold": high_risk_threshold,
                    "risk_interval": interval,
                    "trend_direction": _direction(prediction - global_outcome),
                    "outcome_direction": _direction(outcome_share - global_outcome),
                    "trend_matches_outcome": (
                        _direction(prediction - global_outcome)
                        == _direction(outcome_share - global_outcome)
                    ),
                    "interval_contains_outcome": (
                        interval["p10"] <= outcome_share <= interval["p90"]
                    ),
                    "observed_high_risk": observed_high,
                    "predicted_high_risk": predicted_high,
                    "false_alarm": predicted_high and not observed_high,
                    "static_prior_missed_high_risk": static_miss,
                    "static_prior_miss_recovered": static_miss and predicted_high,
                    "field_outcome_validated": False,
                    "runtime_default_allowed": False,
                }
            )
    return rows


def _global_risk_share(hps_ingestion: dict[str, Any], outcome: str) -> float:
    distribution = hps_ingestion["outcome_summary"][outcome]["response_distribution"]
    risk_codes = _risk_proxy_codes(distribution)
    return round(sum(float(distribution[code]) for code in risk_codes), 6)


def _risk_proxy_codes(distribution: dict[str, Any]) -> set[str]:
    numeric_codes = []
    for value in distribution:
        try:
            numeric_codes.append((float(value), value))
        except ValueError:
            continue
    if not numeric_codes:
        return set(distribution)
    numeric_codes.sort()
    threshold = numeric_codes[len(numeric_codes) // 2][0]
    return {code for numeric, code in numeric_codes if numeric >= threshold}


def _external_holdout_summary(
    *,
    holdout_cases: list[dict[str, Any]],
    segment_columns: list[str],
) -> dict[str, Any]:
    return {
        "case_count": len(holdout_cases),
        "segment_columns": segment_columns,
        "source_signal": SOURCE_SIGNAL,
        "holdout_outcome_proxy": HOLDOUT_OUTCOME,
        "observed_high_risk_case_count": sum(
            1 for case in holdout_cases if case["observed_high_risk"]
        ),
        "predicted_high_risk_case_count": sum(
            1 for case in holdout_cases if case["predicted_high_risk"]
        ),
    }


def _static_prior_metrics(cases: list[dict[str, Any]]) -> dict[str, float]:
    case_count = len(cases)
    return {
        "trend_direction_accuracy": _rate(
            sum(1 for case in cases if case["outcome_direction"] == "stable"),
            case_count,
        ),
        "interval_coverage": _rate(
            sum(
                1
                for case in cases
                if _risk_interval(case["static_prior_prediction"])["p10"]
                <= case["holdout_outcome_proxy"]
                <= _risk_interval(case["static_prior_prediction"])["p90"]
            ),
            case_count,
        ),
        "risk_ranking_quality": 0.0,
        "false_alarm_rate": 0.0,
        "static_prior_miss_recovery_rate": 0.0,
        "abnormal_segment_recall": 0.0,
    }


def _r11_metrics(cases: list[dict[str, Any]]) -> dict[str, float]:
    case_count = len(cases)
    flagged = [case for case in cases if case["predicted_high_risk"]]
    false_alarms = [case for case in flagged if case["false_alarm"]]
    static_misses = [case for case in cases if case["static_prior_missed_high_risk"]]
    recovered = [case for case in static_misses if case["static_prior_miss_recovered"]]
    return {
        "trend_direction_accuracy": _rate(
            sum(1 for case in cases if case["trend_matches_outcome"]),
            case_count,
        ),
        "interval_coverage": _rate(
            sum(1 for case in cases if case["interval_contains_outcome"]),
            case_count,
        ),
        "risk_ranking_quality": _risk_ranking_quality(cases),
        "false_alarm_rate": _rate(len(false_alarms), len(flagged)),
        "static_prior_miss_recovery_rate": _rate(len(recovered), len(static_misses)),
        "abnormal_segment_recall": _abnormal_segment_recall(cases),
    }


def _risk_ranking_quality(cases: list[dict[str, Any]]) -> float:
    top_k = min(2, len(cases))
    predicted_top = {
        case["case_id"]
        for case in sorted(cases, key=lambda item: item["r11_prediction"], reverse=True)[
            :top_k
        ]
    }
    observed_top = {
        case["case_id"]
        for case in sorted(
            cases,
            key=lambda item: item["holdout_outcome_proxy"],
            reverse=True,
        )[:top_k]
    }
    return _rate(len(predicted_top.intersection(observed_top)), top_k)


def _abnormal_segment_recall(cases: list[dict[str, Any]]) -> float:
    observed = {case["case_id"] for case in cases if case["observed_high_risk"]}
    if not observed:
        return 0.0
    predicted = {case["case_id"] for case in cases if case["predicted_high_risk"]}
    return _rate(len(observed.intersection(predicted)), len(observed))


def _failure_reasons(metrics: dict[str, float]) -> list[str]:
    reasons = []
    if metrics["risk_ranking_quality"] < EXTERNAL_HOLDOUT_FLOORS["risk_ranking_quality"]:
        reasons.append("risk_ranking_quality_below_external_holdout_floor")
    if metrics["interval_coverage"] < EXTERNAL_HOLDOUT_FLOORS["interval_coverage"]:
        reasons.append("interval_coverage_below_external_holdout_floor")
    if metrics["false_alarm_rate"] > EXTERNAL_HOLDOUT_FLOORS["false_alarm_rate"]:
        reasons.append("false_alarm_rate_above_external_holdout_ceiling")
    if (
        metrics["static_prior_miss_recovery_rate"]
        < EXTERNAL_HOLDOUT_FLOORS["static_prior_miss_recovery_rate"]
    ):
        reasons.append("static_prior_miss_recovery_below_external_holdout_floor")
    if (
        metrics["abnormal_segment_recall"]
        < EXTERNAL_HOLDOUT_FLOORS["abnormal_segment_recall"]
    ):
        reasons.append("abnormal_segment_recall_below_external_holdout_floor")
    return reasons


def _risk_interval(prediction: float) -> dict[str, float]:
    return {
        "p10": round(_clip(prediction - INTERVAL_HALF_WIDTH, 0.0, 1.0), 6),
        "median": round(prediction, 6),
        "p90": round(_clip(prediction + INTERVAL_HALF_WIDTH, 0.0, 1.0), 6),
    }


def _direction(delta: float) -> str:
    if delta > TREND_EPSILON:
        return "increase"
    if delta < -TREND_EPSILON:
        return "decrease"
    return "stable"


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 3)


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r11-path", required=True)
    parser.add_argument("--hps-ingestion-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r11_external_holdout_validation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r11_interaction_risk_discoverer=load_json_artifact(args.r11_path),
        hps_ingestion=load_json_artifact(args.hps_ingestion_path),
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
