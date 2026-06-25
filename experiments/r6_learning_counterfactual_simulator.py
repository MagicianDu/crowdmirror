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
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_LEARNING_COUNTERFACTUAL_SIMULATOR_SCHEMA_VERSION = (
    "r6-learning-counterfactual-simulator-v1"
)

HIGH_RISK_THRESHOLD = 0.40
INTERACTION_DELTA_THRESHOLD = 0.03
MAX_MECHANISM_AMPLIFICATION = 1.80


def build_r6_learning_counterfactual_simulator(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id=f"{artifact_id}-trend-interval-risk",
        run_id=run_id,
    )
    learned_weights = _learn_mechanism_weights(metrics["case_results"])
    case_results = [
        _case_result(case=case, learned_weights=learned_weights)
        for case in metrics["case_results"]
    ]
    summary = _summary(case_results, raw_summary=metrics["summary"])
    positive_signal = (
        summary["learned_operator_false_alarm_rate"]
        < summary["raw_interaction_false_alarm_rate"]
        and summary["static_prior_miss_recovery_rate"] >= 1.0
    )
    report = {
        "schema_version": R6_LEARNING_COUNTERFACTUAL_SIMULATOR_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "learning_counterfactual_simulator_guarded_positive_signal"
            if positive_signal
            else "learning_counterfactual_simulator_diagnostic_only"
        ),
        "claim_status": "guarded_diagnostic",
        "method_definition": {
            "method_name": "outcome_residual_weighted_counterfactual_simulator",
            "learning_signal": (
                "Estimate mechanism-level amplification weights from observed/proxy "
                "residuals relative to static prior and raw interaction deltas."
            ),
            "counterfactual_role": (
                "Rank scenario mitigation policies by expected reject-risk reduction "
                "under the learned mechanism weights."
            ),
            "static_prior_role": "foundation_not_opponent",
            "field_outcome_required_for_runtime_default": True,
        },
        "learned_mechanism_weights": _sorted_weight_rows(learned_weights),
        "summary": summary,
        "case_results": case_results,
        "product_support_delta": {
            "supports_product_values": [
                "risk_distribution",
                "abnormal_segments",
                "mechanism_explanation",
                "counterfactual_policy_comparison",
                "false_alarm_control",
            ],
            "unsupported_product_values": [
                "field_validated_trend_direction",
                "runtime_default_update",
            ],
            "support_boundary": (
                "This artifact strengthens Product risk discovery and policy comparison "
                "claims only at current-proxy diagnostic level."
            ),
        },
        "acceptance_gates": {
            "learned_mechanism_weights_present": bool(learned_weights),
            "learned_operator_reduces_false_alarm_vs_raw_interaction": (
                summary["learned_operator_false_alarm_rate"]
                < summary["raw_interaction_false_alarm_rate"]
            ),
            "static_prior_miss_recovery_preserved": (
                summary["static_prior_miss_recovery_rate"] >= 1.0
            ),
            "counterfactual_policy_rankings_present": all(
                case["counterfactual_policy_results"] for case in case_results
            ),
            "current_proxy_positive_signal": positive_signal,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            metrics["artifact_id"],
            *[
                source_ref
                for case in case_results
                for source_ref in case["source_artifact_ids"]
            ],
        ],
        "allowed_claims": [
            "Research can report a guarded current-proxy positive signal for false-alarm reduction.",
            "Product can compare counterfactual mitigation policies as diagnostic decision support.",
            "Mechanism weights can be inspected as outcome-residual learning evidence.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "精准预测系统",
            "系统可以精确预测单点结果",
            "learned operator is field validated",
            "learned operator can be enabled by default",
        ],
        "blocking_gaps": [
            "needs_independent_holdout_for_learned_mechanism_weights",
            "needs_customer_or_field_outcome_feedback",
            "needs_runtime_default_guard_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_learning_counterfactual_simulator(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_learning_counterfactual_simulator(**kwargs),
    )


def _learn_mechanism_weights(
    case_results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    evidence: dict[str, list[dict[str, Any]]] = {}
    for case in case_results:
        static = float(case["static_prior_prediction"])
        interaction = float(case["interaction_prediction"])
        observed = float(case["observed_reject_proxy"])
        raw_delta = interaction - static
        if raw_delta <= 0:
            continue
        ratio = _clip((observed - static) / raw_delta, 0.0, MAX_MECHANISM_AMPLIFICATION)
        for segment in case["top_abnormal_segments"]:
            for mechanism_id in segment["mechanisms"]:
                mechanism_ratio = 0.0 if mechanism_id == "official_trust_buffer" else ratio
                evidence.setdefault(mechanism_id, []).append(
                    {
                        "source_key": case["source_key"],
                        "target_case_id": case["target_case_id"],
                        "residual_to_delta_ratio": round(mechanism_ratio, 3),
                        "segment_delta_reject": segment["delta_reject"],
                    }
                )
    weights: dict[str, dict[str, Any]] = {}
    for mechanism_id, rows in evidence.items():
        learned_weight = round(
            sum(row["residual_to_delta_ratio"] for row in rows) / len(rows),
            3,
        )
        weights[mechanism_id] = {
            "mechanism_id": mechanism_id,
            "learned_weight": learned_weight,
            "evidence_case_count": len({row["source_key"] for row in rows}),
            "evidence_source_keys": _unique(row["source_key"] for row in rows),
            "update_direction": _update_direction(learned_weight),
            "learning_rule": "clipped_outcome_residual_to_interaction_delta_ratio",
        }
    return weights


def _case_result(
    *,
    case: dict[str, Any],
    learned_weights: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    static = float(case["static_prior_prediction"])
    interaction = float(case["interaction_prediction"])
    observed = float(case["observed_reject_proxy"])
    raw_delta = round(interaction - static, 3)
    weighted_delta = _weighted_delta(case, learned_weights)
    learned_prediction = round(_clip(static + weighted_delta, 0.0, 1.0), 3)
    observed_high_risk = observed >= HIGH_RISK_THRESHOLD
    static_missed_high_risk = (
        observed_high_risk
        and static < HIGH_RISK_THRESHOLD
        and observed - static >= 0.05
    )
    raw_flags = raw_delta >= INTERACTION_DELTA_THRESHOLD
    learned_flags = weighted_delta >= INTERACTION_DELTA_THRESHOLD
    raw_false_alarm = raw_flags and not observed_high_risk
    learned_false_alarm = learned_flags and not observed_high_risk
    policies = _rank_counterfactual_policies(
        static_prediction=static,
        learned_delta=weighted_delta,
        observed_reject_proxy=observed,
    )
    return {
        "source_key": case["source_key"],
        "target_case_id": case["target_case_id"],
        "source_artifact_ids": [case["source_ablation_artifact_id"]],
        "static_prior_prediction": round(static, 3),
        "raw_interaction_prediction": round(interaction, 3),
        "learned_operator_prediction": learned_prediction,
        "observed_reject_proxy": round(observed, 3),
        "raw_interaction_delta": raw_delta,
        "learned_operator_delta": round(weighted_delta, 3),
        "observed_high_risk": observed_high_risk,
        "static_prior_missed_high_risk": static_missed_high_risk,
        "raw_interaction_flags_new_risk": raw_flags,
        "learned_operator_flags_new_risk": learned_flags,
        "raw_interaction_false_alarm": raw_false_alarm,
        "learned_operator_false_alarm": learned_false_alarm,
        "learned_mechanism_contributions": _mechanism_contributions(
            case,
            learned_weights,
        ),
        "counterfactual_policy_results": policies,
        "claim_status": "guarded_diagnostic",
    }


def _weighted_delta(
    case: dict[str, Any],
    learned_weights: dict[str, dict[str, Any]],
) -> float:
    raw_delta = float(case["interaction_prediction"]) - float(case["static_prior_prediction"])
    segment_delta_sum = sum(
        float(segment["delta_reject"]) for segment in case["top_abnormal_segments"]
    )
    if raw_delta <= 0 or segment_delta_sum <= 0:
        return 0.0
    weighted_sum = 0.0
    for segment in case["top_abnormal_segments"]:
        weights = [
            learned_weights[mechanism]["learned_weight"]
            for mechanism in segment["mechanisms"]
            if mechanism in learned_weights
        ]
        average_weight = sum(weights) / len(weights) if weights else 0.0
        weighted_sum += float(segment["delta_reject"]) * average_weight
    return round(raw_delta * (weighted_sum / segment_delta_sum), 3)


def _mechanism_contributions(
    case: dict[str, Any],
    learned_weights: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    contributions = []
    for segment in case["top_abnormal_segments"]:
        for mechanism_id in segment["mechanisms"]:
            if mechanism_id not in learned_weights:
                continue
            weight = learned_weights[mechanism_id]["learned_weight"]
            contributions.append(
                {
                    "segment_id": segment["segment_id"],
                    "mechanism_id": mechanism_id,
                    "raw_segment_delta": segment["delta_reject"],
                    "learned_weight": weight,
                    "weighted_segment_delta": round(segment["delta_reject"] * weight, 3),
                }
            )
    return contributions


def _rank_counterfactual_policies(
    *,
    static_prediction: float,
    learned_delta: float,
    observed_reject_proxy: float,
) -> list[dict[str, Any]]:
    policies = [
        {
            "policy_id": "targeted_mitigation",
            "attenuation": 0.55,
            "mechanism_action": "reduce loss salience and substitution pressure for high-risk segments",
        },
        {
            "policy_id": "phased_release",
            "attenuation": 0.70,
            "mechanism_action": "spread shock over time and allow early feedback",
        },
        {
            "policy_id": "trust_repair_message",
            "attenuation": 0.82,
            "mechanism_action": "reduce trust-shock propagation through explanation and appeal channels",
        },
        {
            "policy_id": "no_mitigation",
            "attenuation": 1.00,
            "mechanism_action": "keep the original scenario unchanged",
        },
    ]
    results = []
    for policy in policies:
        predicted = round(
            _clip(static_prediction + learned_delta * policy["attenuation"], 0.0, 1.0),
            3,
        )
        risk_reduction = round(max(0.0, learned_delta * (1 - policy["attenuation"])), 3)
        calibration_penalty = round(abs(predicted - observed_reject_proxy), 3)
        score = round(1.0 - predicted + risk_reduction - calibration_penalty * 0.25, 3)
        results.append(
            {
                "policy_id": policy["policy_id"],
                "predicted_reject_proxy": predicted,
                "risk_reduction_vs_no_mitigation": risk_reduction,
                "decision_value_score": score,
                "mechanism_action": policy["mechanism_action"],
            }
        )
    ranked = sorted(
        results,
        key=lambda item: (
            item["decision_value_score"],
            -item["predicted_reject_proxy"],
        ),
        reverse=True,
    )
    return [
        {
            "rank": index,
            **item,
        }
        for index, item in enumerate(ranked, start=1)
    ]


def _summary(
    case_results: list[dict[str, Any]],
    *,
    raw_summary: dict[str, Any],
) -> dict[str, Any]:
    raw_flagged = [
        case for case in case_results if case["raw_interaction_flags_new_risk"]
    ]
    learned_flagged = [
        case for case in case_results if case["learned_operator_flags_new_risk"]
    ]
    raw_false_alarms = [
        case for case in raw_flagged if case["raw_interaction_false_alarm"]
    ]
    learned_false_alarms = [
        case for case in learned_flagged if case["learned_operator_false_alarm"]
    ]
    static_misses = [
        case for case in case_results if case["static_prior_missed_high_risk"]
    ]
    recovered_misses = [
        case for case in static_misses if case["learned_operator_flags_new_risk"]
    ]
    high_risk_learned_flags = [
        case for case in learned_flagged if case["observed_high_risk"]
    ]
    raw_error = sum(
        abs(case["raw_interaction_prediction"] - case["observed_reject_proxy"])
        for case in case_results
    ) / len(case_results)
    learned_error = sum(
        abs(case["learned_operator_prediction"] - case["observed_reject_proxy"])
        for case in case_results
    ) / len(case_results)
    return {
        "case_count": len(case_results),
        "raw_interaction_false_alarm_rate": raw_summary["false_alarm_rate"],
        "learned_operator_false_alarm_rate": _rate(
            len(learned_false_alarms),
            len(learned_flagged),
        ),
        "raw_interaction_flagged_case_count": len(raw_flagged),
        "learned_operator_flagged_case_count": len(learned_flagged),
        "learned_operator_top_k_hit_rate": _rate(
            len(high_risk_learned_flags),
            len(learned_flagged),
        ),
        "static_prior_miss_recovery_rate": _rate(
            len(recovered_misses),
            len(static_misses),
        ),
        "mean_raw_interaction_absolute_error": round(raw_error, 3),
        "mean_learned_operator_absolute_error": round(learned_error, 3),
        "mean_error_reduction_vs_raw_interaction": round(raw_error - learned_error, 3),
        "counterfactual_policy_count": len(
            {
                policy["policy_id"]
                for case in case_results
                for policy in case["counterfactual_policy_results"]
            }
        ),
    }


def _sorted_weight_rows(weights: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        weights.values(),
        key=lambda item: (item["update_direction"], item["mechanism_id"]),
    )


def _update_direction(learned_weight: float) -> str:
    if learned_weight > 1.0:
        return "amplify"
    if learned_weight < 1.0:
        return "attenuate"
    return "keep"


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _unique(values: Any) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_learning_counterfactual_simulator(
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
