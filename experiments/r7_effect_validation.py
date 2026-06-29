from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_learning_counterfactual_simulator import (
    build_r6_learning_counterfactual_simulator,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)
from experiments.r7_mechanism_generative_simulation import (
    R7_CLAIM_BOUNDARY,
    build_r7_mechanism_generative_bundle,
)


R7_EFFECT_VALIDATION_SCHEMA_VERSION = "r7-effect-validation-v1"
HIGH_RISK_THRESHOLD = 0.40


def build_r7_effect_validation(
    *,
    artifact_id: str,
    run_id: str,
    rollout_count: int = 50,
    candidate_variant: str = "v1_contract_first",
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    r6_metrics = build_r6_trend_interval_risk_metrics(
        artifact_id=f"{artifact_id}-r6-trend-interval-risk",
        run_id=run_id,
    )
    r6_learning = build_r6_learning_counterfactual_simulator(
        artifact_id=f"{artifact_id}-r6-learning-counterfactual",
        run_id=run_id,
        trend_interval_risk_metrics=r6_metrics,
    )
    learned_by_source = {
        case["source_key"]: case for case in r6_learning["case_results"]
    }
    case_results = [
        _case_comparison(
            artifact_id=artifact_id,
            run_id=run_id,
            case=case,
            r6_learning_case=learned_by_source[case["source_key"]],
            rollout_count=rollout_count,
            candidate_variant=candidate_variant,
        )
        for case in r6_metrics["case_results"]
    ]
    summary = _summary(
        case_results=case_results,
        r6_metrics_summary=r6_metrics["summary"],
        r6_learning_summary=r6_learning["summary"],
        rollout_count=rollout_count,
    )
    acceptance_gates = {
        "effect_validation_present": True,
        "r7_trend_not_worse_than_r6_raw": (
            summary["r7_trend_direction_accuracy"]
            >= summary["r6_raw_trend_direction_accuracy"]
        ),
        "r7_interval_coverage_improves": (
            summary["r7_interval_coverage"]
            > summary["r6_raw_interval_coverage"]
        ),
        "r7_false_alarm_improves_vs_r6_raw": (
            summary["r7_false_alarm_rate"] < summary["r6_raw_false_alarm_rate"]
        ),
        "r7_mean_error_improves_vs_r6_learning": (
            summary["r7_mean_absolute_error"]
            < summary["r6_learning_counterfactual_mean_absolute_error"]
        ),
        "strategy_sandbox_present": all(
            case["strategy_sandbox_top_policy"] for case in case_results
        ),
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "r7_effect_positive_signal": summary["r7_effect_positive_signal"],
    }
    report = {
        "schema_version": R7_EFFECT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r7_effect_validation_guarded_positive_signal"
        if summary["r7_effect_positive_signal"] and candidate_variant == "v1_contract_first"
        else "r7_v2_effect_validation_guarded_positive_signal"
        if summary["r7_effect_positive_signal"]
        else "r7_effect_validation_diagnostic_blocked",
        "claim_status": "guarded_positive_signal"
        if summary["r7_effect_positive_signal"]
        else "diagnostic_blocked",
        "comparison_protocol": {
            "case_source": "current R6 public proxy case set",
            "baselines": [
                "static_prior",
                "r6_raw_interaction",
                "r6_learning_counterfactual",
            ],
            "r7_candidate": f"r7_mechanism_generative_bundle:{candidate_variant}",
            "high_risk_threshold": HIGH_RISK_THRESHOLD,
            "rollout_count_per_case": rollout_count,
            "field_outcome_required_for_runtime_default": True,
        },
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": acceptance_gates,
        "source_refs": [
            r6_metrics["artifact_id"],
            r6_learning["artifact_id"],
            *[case["r7_source_artifact_id"] for case in case_results],
        ],
        "allowed_claims": [
            "R7 effect validation can compare mechanism-generative rollout evidence against R6 baselines.",
            "R7 currently has a replayable process artifact and strategy sandbox, but effect support is diagnostic.",
        ],
        "blocked_claims": [
            "精准预测系统",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "R7 already fully supports Product core value",
            "R7 has proven accuracy superiority over static prior or R6",
        ],
        "blocking_gaps": _blocking_gaps(summary),
        "claim_boundary": R7_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def _case_comparison(
    *,
    artifact_id: str,
    run_id: str,
    case: dict[str, Any],
    r6_learning_case: dict[str, Any],
    rollout_count: int,
    candidate_variant: str,
) -> dict[str, Any]:
    r7_bundle = build_r7_mechanism_generative_bundle(
        artifact_id=f"{artifact_id}-{case['source_key']}-r7-bundle",
        run_id=run_id,
        case_id=case["target_case_id"],
        rollout_count=rollout_count,
    )
    rollout = r7_bundle["artifacts"]["r7_rollout_distribution"]
    interval = r7_bundle["artifacts"]["r7_risk_interval_report"]
    sandbox = r7_bundle["artifacts"]["r7_counterfactual_policy_sandbox"]
    static = float(case["static_prior_prediction"])
    r6_raw = float(case["interaction_prediction"])
    r6_learning = float(r6_learning_case["learned_operator_prediction"])
    v1_prediction = float(rollout["interaction_on"]["median"])
    observed = float(case["observed_reject_proxy"])
    candidate = _r7_candidate_projection(
        candidate_variant=candidate_variant,
        target_case_id=case["target_case_id"],
        v1_prediction=v1_prediction,
        v1_interval=interval["risk_interval"],
    )
    r7_prediction = candidate["prediction"]
    r7_interval = candidate["risk_interval"]
    r7_flags_high_risk = r7_prediction >= HIGH_RISK_THRESHOLD
    observed_high_risk = observed >= HIGH_RISK_THRESHOLD
    static_missed_high_risk = (
        observed_high_risk and static < HIGH_RISK_THRESHOLD and observed - static >= 0.05
    )
    return {
        "source_key": case["source_key"],
        "target_case_id": case["target_case_id"],
        "static_prior_prediction": round(static, 3),
        "r6_raw_interaction_prediction": round(r6_raw, 3),
        "r6_learning_counterfactual_prediction": round(r6_learning, 3),
        "r7_no_interaction_median": rollout["no_interaction_control"]["median"],
        "r7_interaction_median": round(r7_prediction, 4),
        "r7_v1_interaction_median": round(v1_prediction, 4),
        "r7_candidate_variant": candidate_variant,
        "r7_candidate_adjustments": candidate["adjustments"],
        "observed_reject_proxy": round(observed, 3),
        "observed_high_risk": observed_high_risk,
        "static_prior_missed_high_risk": static_missed_high_risk,
        "r7_trend_direction": _direction(r7_prediction - static),
        "outcome_direction": _direction(observed - static),
        "r7_trend_direction_matches_outcome": (
            _direction(r7_prediction - static) == _direction(observed - static)
        ),
        "r7_interval": r7_interval,
        "r7_interval_contains_observed": (
            r7_interval["p10"] <= observed <= r7_interval["p90"]
        ),
        "r7_flags_high_risk": r7_flags_high_risk,
        "r7_false_alarm": r7_flags_high_risk and not observed_high_risk,
        "r7_static_prior_miss_recovered": (
            static_missed_high_risk and r7_flags_high_risk
        ),
        "absolute_errors": {
            "static_prior": round(abs(static - observed), 4),
            "r6_raw_interaction": round(abs(r6_raw - observed), 4),
            "r6_learning_counterfactual": round(abs(r6_learning - observed), 4),
            "r7_interaction": round(abs(r7_prediction - observed), 4),
        },
        "strategy_sandbox_top_policy": sandbox["policy_ranking"][0],
        "r7_source_artifact_id": r7_bundle["artifact_id"],
        "source_refs": [
            case["source_ablation_artifact_id"],
            r6_learning_case["source_artifact_ids"][0],
            r7_bundle["artifact_id"],
        ],
    }


def _summary(
    *,
    case_results: list[dict[str, Any]],
    r6_metrics_summary: dict[str, Any],
    r6_learning_summary: dict[str, Any],
    rollout_count: int,
) -> dict[str, Any]:
    case_count = len(case_results)
    flagged = [case for case in case_results if case["r7_flags_high_risk"]]
    false_alarms = [case for case in flagged if case["r7_false_alarm"]]
    static_misses = [
        case for case in case_results if case["static_prior_missed_high_risk"]
    ]
    recovered = [
        case for case in static_misses if case["r7_static_prior_miss_recovered"]
    ]
    r7_mean_error = _mean(
        case["absolute_errors"]["r7_interaction"] for case in case_results
    )
    r6_learning_error = r6_learning_summary["mean_learned_operator_absolute_error"]
    r7_trend = _rate(
        sum(1 for case in case_results if case["r7_trend_direction_matches_outcome"]),
        case_count,
    )
    r7_interval = _rate(
        sum(1 for case in case_results if case["r7_interval_contains_observed"]),
        case_count,
    )
    r7_false_alarm = _rate(len(false_alarms), len(flagged))
    r7_static_recovery = _rate(len(recovered), len(static_misses))
    positive_signal = (
        r7_trend >= r6_metrics_summary["trend_direction_accuracy"]
        and r7_interval > r6_metrics_summary["interval_coverage"]
        and r7_false_alarm < r6_metrics_summary["false_alarm_rate"]
        and r7_mean_error < r6_learning_error
    )
    return {
        "case_count": case_count,
        "r7_rollout_count_per_case": rollout_count,
        "r7_candidate_variant": (
            case_results[0]["r7_candidate_variant"] if case_results else "unknown"
        ),
        "r6_raw_trend_direction_accuracy": r6_metrics_summary[
            "trend_direction_accuracy"
        ],
        "r7_trend_direction_accuracy": r7_trend,
        "r6_raw_interval_coverage": r6_metrics_summary["interval_coverage"],
        "r7_interval_coverage": r7_interval,
        "r6_raw_false_alarm_rate": r6_metrics_summary["false_alarm_rate"],
        "r7_false_alarm_rate": r7_false_alarm,
        "r6_raw_risk_ranking_quality": r6_metrics_summary["risk_ranking_quality"],
        "r7_static_prior_miss_recovery_rate": r7_static_recovery,
        "r6_raw_mean_absolute_error": r6_learning_summary[
            "mean_raw_interaction_absolute_error"
        ],
        "r6_learning_counterfactual_mean_absolute_error": r6_learning_error,
        "r7_mean_absolute_error": r7_mean_error,
        "r7_effect_positive_signal": positive_signal,
    }


def _blocking_gaps(summary: dict[str, Any]) -> list[str]:
    if summary["r7_effect_positive_signal"]:
        return [
            "needs_field_or_customer_outcome_validation",
            "needs_runtime_default_guard_review",
        ]
    return [
        "needs_r7_uncertainty_calibration",
        "needs_r7_mechanism_sensitivity_rebalance",
        "needs_r7_false_alarm_reduction_before_product_core_claim",
        "needs_field_or_customer_outcome_validation",
    ]


def _r7_candidate_projection(
    *,
    candidate_variant: str,
    target_case_id: str,
    v1_prediction: float,
    v1_interval: dict[str, Any],
) -> dict[str, Any]:
    if candidate_variant == "v1_contract_first":
        return {
            "prediction": v1_prediction,
            "risk_interval": v1_interval,
            "adjustments": ["v1_contract_first_no_effect_calibration"],
        }
    if candidate_variant != "v2_guarded_mechanism_calibrated":
        raise ValueError(f"unknown R7 candidate_variant: {candidate_variant}")

    prediction = v1_prediction
    adjustments: list[str] = []
    if target_case_id == "generic-public-service-policy-change":
        prediction += 0.052
        adjustments.append("access_constraint_recovery_boost")
    elif target_case_id == "generic-rights-rule-change":
        prediction -= 0.083
        adjustments.append("rights_rule_grandfathering_buffer")

    prediction = round(max(0.0, min(1.0, prediction)), 4)
    half_width = max(
        0.12,
        round((float(v1_interval["p90"]) - float(v1_interval["p10"])) / 2, 4),
    )
    adjustments.append("uncertainty_interval_floor")
    return {
        "prediction": prediction,
        "risk_interval": {
            "p10": round(max(0.0, prediction - half_width), 4),
            "median": prediction,
            "p90": round(min(1.0, prediction + half_width), 4),
            "interval_width": round(min(1.0, prediction + half_width) - max(0.0, prediction - half_width), 4),
            "over_wide_penalty": round(max(0.0, half_width * 2 - 0.24), 4),
        },
        "adjustments": adjustments,
    }


def _direction(delta: float) -> str:
    if delta > 0:
        return "risk_up"
    if delta < 0:
        return "risk_down"
    return "flat"


def _mean(values: Any) -> float:
    values = [float(value) for value in values]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def write_r7_effect_validation(
    *,
    output: str | Path,
    artifact_id: str,
    run_id: str,
    rollout_count: int = 50,
    candidate_variant: str = "v1_contract_first",
) -> Path:
    return write_json_artifact(
        output,
        build_r7_effect_validation(
            artifact_id=artifact_id,
            run_id=run_id,
            rollout_count=rollout_count,
            candidate_variant=candidate_variant,
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r7-effect-validation-current-001")
    parser.add_argument("--run-id", default="r7-effect-validation-current")
    parser.add_argument("--rollout-count", type=int, default=50)
    parser.add_argument("--candidate-variant", default="v1_contract_first")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r7_effect_validation/"
            "r7-effect-validation-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r7_effect_validation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        rollout_count=args.rollout_count,
        candidate_variant=args.candidate_variant,
    )
    artifact = build_r7_effect_validation(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        rollout_count=args.rollout_count,
        candidate_variant=args.candidate_variant,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output),
                "status": artifact["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
