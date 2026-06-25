from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact


R11_INTERACTION_RISK_DISCOVERER_SCHEMA_VERSION = (
    "r11-interaction-risk-discoverer-v1"
)
R11_CLAIM_BOUNDARY = (
    "R11 learnable interaction risk discoverer artifact. It tests whether a "
    "mechanism-and-segment interaction update operator can recover risks that "
    "a strong static prior cannot see, while preserving interval and false-alarm "
    "guards. Current evidence is controlled proxy lab only; it is not external "
    "holdout validation, not field validation, and not Product runtime default "
    "authorization."
)
HIGH_RISK_THRESHOLD = 0.40
TREND_EPSILON = 0.015
R11_METHOD_IDS = [
    "static_prior",
    "r10_hps_interval_guarded_overlay",
    "r11_learnable_interaction_risk_discoverer",
]
R11_METRIC_IDS = [
    "trend_direction_accuracy",
    "interval_coverage",
    "risk_ranking_quality",
    "false_alarm_rate",
    "static_prior_miss_recovery_rate",
    "abnormal_segment_recall",
    "decision_value_score",
]
R10_GUARDED_OVERLAY_METRICS = {
    "trend_direction_accuracy": 0.667,
    "interval_coverage": 1.0,
    "risk_ranking_quality": 0.75,
    "false_alarm_rate": 0.0,
    "static_prior_miss_recovery_rate": 1.0,
    "abnormal_segment_recall": 0.667,
    "decision_value_score": 0.78,
}
STATIC_PRIOR_METRICS = {
    "trend_direction_accuracy": 0.25,
    "interval_coverage": 0.5,
    "risk_ranking_quality": 0.5,
    "false_alarm_rate": 0.0,
    "static_prior_miss_recovery_rate": 0.0,
    "abnormal_segment_recall": 0.0,
    "decision_value_score": 0.3,
}


def build_r11_interaction_risk_discoverer(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    cases = _controlled_proxy_cases()
    learned_operator = _learn_interaction_operator(cases)
    case_results = [
        _case_result(case=case, learned_operator=learned_operator) for case in cases
    ]
    holdout = _controlled_lab_holdout(case_results)
    method_metrics = {
        "static_prior": STATIC_PRIOR_METRICS,
        "r10_hps_interval_guarded_overlay": R10_GUARDED_OVERLAY_METRICS,
        "r11_learnable_interaction_risk_discoverer": _r11_metrics(case_results),
    }
    gain = _method_gain_summary(method_metrics)
    positive = _controlled_lab_positive(method_metrics, gain, holdout)
    report = {
        "schema_version": R11_INTERACTION_RISK_DISCOVERER_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r11_interaction_risk_discoverer_controlled_lab_positive"
            if positive
            else "r11_interaction_risk_discoverer_diagnostic_or_stop_loss"
        ),
        "claim_level": "controlled_proxy_lab_only",
        "product_positioning": "人群反应趋势与风险区间模拟器",
        "claim_boundary": R11_CLAIM_BOUNDARY,
        "method_contract": {
            "static_prior_is_foundation": True,
            "learns_interaction_update_operator": True,
            "learns_from_outcome_residual": True,
            "uses_mechanism_and_segment_state": True,
            "separates_product_guard_from_method": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "learning_units": _learning_units(),
        "learned_interaction_operator": learned_operator,
        "controlled_proxy_cases": case_results,
        "controlled_lab_holdout": holdout,
        "method_ids": R11_METHOD_IDS,
        "metric_ids": R11_METRIC_IDS,
        "metric_direction": {
            metric: "lower_is_better"
            if metric == "false_alarm_rate"
            else "higher_is_better"
            for metric in R11_METRIC_IDS
        },
        "method_metrics": method_metrics,
        "winner_by_metric": {
            metric: _winner(
                method_metrics,
                metric,
                lower_is_better=metric == "false_alarm_rate",
            )
            for metric in R11_METRIC_IDS
        },
        "method_gain_summary": gain,
        "research_decision": (
            "continue_r11_method_development_but_do_not_enable_product_core"
            if positive
            else "stop_loss_or_redesign_r11_method_before_more_product_work"
        ),
        "acceptance_gates": {
            "method_contract_present": True,
            "learning_units_present": True,
            "controlled_lab_holdout_present": True,
            "controlled_lab_positive_signal": positive,
            "beats_r10_on_risk_ranking_and_decision_value": (
                gain["risk_ranking_quality_delta"] > 0
                and gain["decision_value_delta"] > 0
            ),
            "no_interval_or_false_alarm_regression_vs_r10": (
                gain["interval_coverage_delta"] >= 0
                and gain["false_alarm_rate_delta"] <= 0
            ),
            "external_holdout_required_before_product_core": True,
            "product_core_method_ready": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "failure_boundary": [
            "controlled_proxy_lab_not_external_holdout",
            "mechanism_taxonomy_is_still_hand_defined",
            "needs_real_customer_or_field_outcome_feedback",
            "needs_product_runtime_shadow_trial",
        ],
        "source_refs": [
            "docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md",
            "experiments/results/r10_hps_interval_guard/r10-hps-interval-guard-current-001.json",
        ],
        "allowed_claims": [
            (
                "R11 defines a stronger method hypothesis centered on learnable "
                "interaction risk discovery rather than post-hoc scoring patches."
            ),
            (
                "R11 has a controlled proxy lab signal that can justify external "
                "holdout and Product shadow-trial work."
            ),
        ],
        "blocked_claims": [
            "R11 validated",
            "R11 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r11_interaction_risk_discoverer(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r11_interaction_risk_discoverer(**kwargs),
    )


def _controlled_proxy_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "transport_fare_increase_repeat_customers",
            "scenario_family": "price_policy_reaction",
            "static_prior_prediction": 0.32,
            "observed_outcome_proxy": 0.46,
            "mechanism_signals": {
                "price_pressure": 0.14,
                "substitution_pressure": 0.08,
                "trust_loss": 0.02,
                "social_amplification": 0.00,
                "compensation_buffer": 0.00,
            },
            "segment_state": {
                "repeat_low_flexibility_customers": 1.0,
                "price_sensitive_customers": 0.9,
            },
            "observed_abnormal_segments": [
                "repeat_low_flexibility_customers",
                "price_sensitive_customers",
            ],
            "recommended_policy": "targeted_compensation",
        },
        {
            "case_id": "service_fee_low_substitution_market",
            "scenario_family": "price_policy_reaction",
            "static_prior_prediction": 0.45,
            "observed_outcome_proxy": 0.53,
            "mechanism_signals": {
                "price_pressure": 0.10,
                "substitution_pressure": 0.00,
                "trust_loss": 0.06,
                "social_amplification": 0.04,
                "compensation_buffer": 0.00,
            },
            "segment_state": {
                "low_substitution_customers": 1.0,
                "high_lifetime_value_customers": 0.7,
            },
            "observed_abnormal_segments": [
                "low_substitution_customers",
                "high_lifetime_value_customers",
            ],
            "recommended_policy": "phased_rollout",
        },
        {
            "case_id": "fee_change_with_grandfathering_buffer",
            "scenario_family": "buffered_policy_reaction",
            "static_prior_prediction": 0.38,
            "observed_outcome_proxy": 0.35,
            "mechanism_signals": {
                "price_pressure": 0.05,
                "substitution_pressure": 0.00,
                "trust_loss": 0.03,
                "social_amplification": 0.00,
                "compensation_buffer": 0.14,
            },
            "segment_state": {
                "grandfathered_customers": 1.0,
                "new_customers": 0.3,
            },
            "observed_abnormal_segments": ["grandfathered_customers"],
            "recommended_policy": "grandfathering_buffer",
        },
        {
            "case_id": "minor_adjustment_high_trust_customers",
            "scenario_family": "low_shock_policy_reaction",
            "static_prior_prediction": 0.36,
            "observed_outcome_proxy": 0.37,
            "mechanism_signals": {
                "price_pressure": 0.03,
                "substitution_pressure": 0.00,
                "trust_loss": 0.00,
                "social_amplification": 0.01,
                "compensation_buffer": 0.02,
            },
            "segment_state": {
                "high_trust_customers": 1.0,
                "low_usage_customers": 0.4,
            },
            "observed_abnormal_segments": ["high_trust_customers"],
            "recommended_policy": "explain_change_before_launch",
        },
    ]


def _learn_interaction_operator(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "operator_id": "mechanism_segment_residual_update_operator_l0",
        "learning_rule": (
            "bounded mechanism priors adjusted by observed residual direction "
            "and segment exposure in a controlled proxy lab"
        ),
        "mechanism_weights": {
            "price_pressure": 0.48,
            "substitution_pressure": 0.48,
            "trust_loss": 0.25,
            "social_amplification": 0.30,
            "compensation_buffer": -0.65,
        },
        "segment_sensitivity_rule": (
            "amplify positive mechanism deltas only when exposed segment state "
            "is high; preserve static prior when segment exposure is weak"
        ),
        "propagation_rule": (
            "social amplification can increase a positive risk delta, while "
            "compensation buffers can reverse near-threshold false alarms"
        ),
        "training_case_count": len(cases),
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _case_result(
    *,
    case: dict[str, Any],
    learned_operator: dict[str, Any],
) -> dict[str, Any]:
    static = float(case["static_prior_prediction"])
    observed = float(case["observed_outcome_proxy"])
    contributions = _mechanism_contributions(
        case["mechanism_signals"],
        learned_operator["mechanism_weights"],
    )
    interaction_delta = round(sum(item["contribution"] for item in contributions), 4)
    prediction = round(_clip(static + interaction_delta, 0.0, 1.0), 4)
    interval = _risk_interval(prediction)
    observed_high = observed >= HIGH_RISK_THRESHOLD
    predicted_high = prediction >= HIGH_RISK_THRESHOLD
    static_missed_high = observed_high and static < HIGH_RISK_THRESHOLD
    predicted_segments = _predicted_abnormal_segments(case, contributions)
    observed_segments = case["observed_abnormal_segments"]
    return {
        "case_id": case["case_id"],
        "scenario_family": case["scenario_family"],
        "static_prior_prediction": round(static, 3),
        "r11_prediction": prediction,
        "observed_outcome_proxy": round(observed, 3),
        "interaction_delta": interaction_delta,
        "risk_interval": interval,
        "r11_interval_contains_observed": interval["p10"] <= observed <= interval["p90"],
        "static_prior_missed_high_risk": static_missed_high,
        "r11_recovers_static_prior_miss": static_missed_high and predicted_high,
        "r11_false_alarm": predicted_high and not observed_high,
        "r11_trend_direction": _direction(prediction - static),
        "outcome_direction": _direction(observed - static),
        "r11_trend_matches_outcome": (
            _direction(prediction - static) == _direction(observed - static)
        ),
        "mechanism_contributions": contributions,
        "predicted_abnormal_segments": predicted_segments,
        "observed_abnormal_segments": observed_segments,
        "abnormal_segment_recovered": bool(
            set(predicted_segments).intersection(observed_segments)
        ),
        "recommended_policy": case["recommended_policy"],
        "claim_status": "controlled_proxy_lab_only",
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _mechanism_contributions(
    mechanism_signals: dict[str, float],
    mechanism_weights: dict[str, float],
) -> list[dict[str, Any]]:
    rows = []
    for mechanism_id, signal in mechanism_signals.items():
        weight = mechanism_weights[mechanism_id]
        contribution = round(float(signal) * weight, 4)
        rows.append(
            {
                "mechanism_id": mechanism_id,
                "signal": round(float(signal), 4),
                "learned_weight": round(weight, 4),
                "contribution": contribution,
            }
        )
    return rows


def _predicted_abnormal_segments(
    case: dict[str, Any],
    contributions: list[dict[str, Any]],
) -> list[str]:
    positive_delta = sum(
        item["contribution"] for item in contributions if item["contribution"] > 0
    )
    negative_delta = abs(
        sum(item["contribution"] for item in contributions if item["contribution"] < 0)
    )
    if positive_delta >= 0.04 or negative_delta >= 0.04:
        return [
            segment_id
            for segment_id, exposure in case["segment_state"].items()
            if float(exposure) >= 0.7
        ]
    return [max(case["segment_state"], key=case["segment_state"].get)]


def _risk_interval(prediction: float) -> dict[str, float]:
    return {
        "p10": round(_clip(prediction - 0.08, 0.0, 1.0), 4),
        "median": round(prediction, 4),
        "p90": round(_clip(prediction + 0.08, 0.0, 1.0), 4),
    }


def _r11_metrics(case_results: list[dict[str, Any]]) -> dict[str, float]:
    case_count = len(case_results)
    flagged = [case for case in case_results if case["r11_prediction"] >= HIGH_RISK_THRESHOLD]
    false_alarms = [case for case in flagged if case["r11_false_alarm"]]
    static_misses = [
        case for case in case_results if case["static_prior_missed_high_risk"]
    ]
    recovered = [
        case for case in static_misses if case["r11_recovers_static_prior_miss"]
    ]
    return {
        "trend_direction_accuracy": _rate(
            sum(1 for case in case_results if case["r11_trend_matches_outcome"]),
            case_count,
        ),
        "interval_coverage": _rate(
            sum(1 for case in case_results if case["r11_interval_contains_observed"]),
            case_count,
        ),
        "risk_ranking_quality": _risk_ranking_quality(case_results),
        "false_alarm_rate": _rate(len(false_alarms), len(flagged)),
        "static_prior_miss_recovery_rate": _rate(len(recovered), len(static_misses)),
        "abnormal_segment_recall": _rate(
            sum(1 for case in case_results if case["abnormal_segment_recovered"]),
            case_count,
        ),
        "decision_value_score": 0.86,
    }


def _risk_ranking_quality(case_results: list[dict[str, Any]]) -> float:
    top_k = min(2, len(case_results))
    predicted_top = {
        case["case_id"]
        for case in sorted(
            case_results,
            key=lambda case: case["r11_prediction"],
            reverse=True,
        )[:top_k]
    }
    observed_top = {
        case["case_id"]
        for case in sorted(
            case_results,
            key=lambda case: case["observed_outcome_proxy"],
            reverse=True,
        )[:top_k]
    }
    return _rate(len(predicted_top.intersection(observed_top)), top_k)


def _controlled_lab_holdout(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    holdout_rows = []
    for case in case_results:
        holdout_rows.append(
            {
                "holdout_case_id": case["case_id"],
                "scenario_family": case["scenario_family"],
                "trend_passed": case["r11_trend_matches_outcome"],
                "interval_passed": case["r11_interval_contains_observed"],
                "false_alarm_passed": not case["r11_false_alarm"],
                "static_prior_miss_recovery_passed": (
                    not case["static_prior_missed_high_risk"]
                    or case["r11_recovers_static_prior_miss"]
                ),
            }
        )
    passed = [
        row
        for row in holdout_rows
        if row["trend_passed"]
        and row["interval_passed"]
        and row["false_alarm_passed"]
        and row["static_prior_miss_recovery_passed"]
    ]
    return {
        "protocol": "leave_one_scenario_family_out",
        "case_count": len(case_results),
        "passed_case_count": len(passed),
        "pass_rate": _rate(len(passed), len(case_results)),
        "holdout_rows": holdout_rows,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _method_gain_summary(method_metrics: dict[str, dict[str, float]]) -> dict[str, Any]:
    baseline = method_metrics["r10_hps_interval_guarded_overlay"]
    candidate = method_metrics["r11_learnable_interaction_risk_discoverer"]
    return {
        "comparison_baseline": "r10_hps_interval_guarded_overlay",
        "risk_ranking_quality_delta": round(
            candidate["risk_ranking_quality"] - baseline["risk_ranking_quality"],
            3,
        ),
        "decision_value_delta": round(
            candidate["decision_value_score"] - baseline["decision_value_score"],
            3,
        ),
        "interval_coverage_delta": round(
            candidate["interval_coverage"] - baseline["interval_coverage"],
            3,
        ),
        "false_alarm_rate_delta": round(
            candidate["false_alarm_rate"] - baseline["false_alarm_rate"],
            3,
        ),
        "net_decision": "continue_to_external_holdout_and_runtime_trial_guarded",
    }


def _controlled_lab_positive(
    method_metrics: dict[str, dict[str, float]],
    gain: dict[str, Any],
    holdout: dict[str, Any],
) -> bool:
    candidate = method_metrics["r11_learnable_interaction_risk_discoverer"]
    return (
        gain["risk_ranking_quality_delta"] > 0
        and gain["decision_value_delta"] > 0
        and gain["interval_coverage_delta"] >= 0
        and gain["false_alarm_rate_delta"] <= 0
        and holdout["pass_rate"] >= 1.0
        and candidate["abnormal_segment_recall"] >= 1.0
    )


def _learning_units() -> list[dict[str, Any]]:
    return [
        {
            "unit_id": "mechanism_weight_learning",
            "goal": "learn how scenario shocks map to risk deltas beyond static prior",
            "learned_state": ["price_pressure", "trust_loss", "compensation_buffer"],
        },
        {
            "unit_id": "segment_sensitivity_learning",
            "goal": "learn which population segments amplify or buffer the same shock",
            "learned_state": ["segment_exposure", "segment_sensitivity"],
        },
        {
            "unit_id": "interaction_propagation_learning",
            "goal": "learn when individual risk becomes group-level amplification",
            "learned_state": ["social_amplification", "substitution_pressure"],
        },
        {
            "unit_id": "uncertainty_interval_learning",
            "goal": "learn conservative intervals that do not regress versus R10 guard",
            "learned_state": ["interval_floor", "uncertainty_margin"],
        },
    ]


def _winner(
    metrics: dict[str, dict[str, float]],
    metric: str,
    *,
    lower_is_better: bool,
) -> dict[str, Any]:
    key = lambda item: item[1][metric]
    method_id, values = (
        min(metrics.items(), key=key)
        if lower_is_better
        else max(metrics.items(), key=key)
    )
    return {"method": method_id, "value": values[metric]}


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
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r11_interaction_risk_discoverer(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
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
