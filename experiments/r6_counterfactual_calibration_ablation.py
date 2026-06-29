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
from experiments.r6_learning_counterfactual_holdout_validation import (
    UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR,
    _apply_risk_preserving_calibration,
)
from experiments.r6_learning_counterfactual_simulator import (
    _case_result,
    _learn_mechanism_weights,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_COUNTERFACTUAL_CALIBRATION_ABLATION_SCHEMA_VERSION = (
    "r6-counterfactual-calibration-ablation-v1"
)
SELECTED_VARIANT_ID = "floor_plus_non_regression_calibration"


def build_r6_counterfactual_calibration_ablation(
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
    variants = [
        _evaluate_variant(
            variant_id="learned_weights_only",
            case_results=metrics["case_results"],
            unknown_mechanism_weight=0.0,
            risk_preserving_calibration_enabled=False,
        ),
        _evaluate_variant(
            variant_id="unseen_floor_only",
            case_results=metrics["case_results"],
            unknown_mechanism_weight=UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR,
            risk_preserving_calibration_enabled=False,
        ),
        _evaluate_variant(
            variant_id=SELECTED_VARIANT_ID,
            case_results=metrics["case_results"],
            unknown_mechanism_weight=UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR,
            risk_preserving_calibration_enabled=True,
        ),
    ]
    selected = _variant_by_id(variants, SELECTED_VARIANT_ID)
    stress_grid = _stress_grid(metrics["case_results"])
    report = {
        "schema_version": R6_COUNTERFACTUAL_CALIBRATION_ABLATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "counterfactual_calibration_ablation_guarded_supported"
        if _passes_holdout_gate(selected)
        else "counterfactual_calibration_ablation_diagnostic_blocked",
        "selected_variant_id": SELECTED_VARIANT_ID,
        "variant_results": variants,
        "stress_grid_results": stress_grid,
        "summary": {
            "variant_count": len(variants),
            "stress_grid_count": len(stress_grid),
            "selected_variant_summary": selected["summary"],
            "passing_stress_config_count": sum(
                1 for item in stress_grid if item["passes_current_proxy_holdout_gate"]
            ),
        },
        "acceptance_gates": {
            "ablation_variants_present": len(variants) >= 3,
            "selected_variant_non_regression_passed": selected["summary"][
                "non_regression_rate"
            ]
            >= 0.80,
            "selected_variant_false_alarm_reduction_passed": selected["summary"][
                "false_alarm_reduction_rate"
            ]
            >= 0.80,
            "selected_variant_static_miss_recovery_passed": selected["summary"][
                "static_prior_miss_recovery_rate"
            ]
            >= 0.80,
            "current_proxy_holdout_gate_passed": _passes_holdout_gate(selected),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [metrics["artifact_id"]],
        "allowed_claims": [
            "Ablation can attribute current-proxy holdout gains to the unseen mechanism floor plus non-regression calibration.",
            "Stress grid can be used as diagnostic evidence for parameter sensitivity.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "calibration is proven beyond current proxy holdout",
        ],
        "blocking_gaps": [
            "needs_field_or_customer_outcome_validation",
            "needs_stricter_cross_source_holdout",
            "needs_runtime_default_guard_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_counterfactual_calibration_ablation(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_counterfactual_calibration_ablation(**kwargs),
    )


def _evaluate_variant(
    *,
    variant_id: str,
    case_results: list[dict[str, Any]],
    unknown_mechanism_weight: float,
    risk_preserving_calibration_enabled: bool,
) -> dict[str, Any]:
    trials = _variant_trials(
        case_results=case_results,
        unknown_mechanism_weight=unknown_mechanism_weight,
        risk_preserving_calibration_enabled=risk_preserving_calibration_enabled,
    )
    summary = _summary(trials)
    variant = {
        "variant_id": variant_id,
        "unknown_mechanism_weight": unknown_mechanism_weight,
        "risk_preserving_calibration_enabled": risk_preserving_calibration_enabled,
        "summary": summary,
        "holdout_trials": trials,
        "passes_current_proxy_holdout_gate": _summary_passes_holdout_gate(summary),
        "component_contribution": _component_contribution(
            variant_id=variant_id,
            summary=summary,
        ),
    }
    assert_strict_json(variant)
    return variant


def _variant_trials(
    *,
    case_results: list[dict[str, Any]],
    unknown_mechanism_weight: float,
    risk_preserving_calibration_enabled: bool,
) -> list[dict[str, Any]]:
    trials = []
    for heldout in case_results:
        train_cases = [
            case for case in case_results if case["source_key"] != heldout["source_key"]
        ]
        weights = _learn_mechanism_weights(train_cases)
        learned = _case_result(
            case=heldout,
            learned_weights=weights,
            unknown_mechanism_weight=unknown_mechanism_weight,
        )
        if risk_preserving_calibration_enabled:
            learned = _apply_risk_preserving_calibration(learned)
        raw_error = round(
            abs(learned["raw_interaction_prediction"] - learned["observed_reject_proxy"]),
            3,
        )
        learned_error = round(
            abs(learned["learned_operator_prediction"] - learned["observed_reject_proxy"]),
            3,
        )
        return_trial = {
            "heldout_source_key": heldout["source_key"],
            "train_source_keys": [case["source_key"] for case in train_cases],
            "raw_interaction_prediction": learned["raw_interaction_prediction"],
            "learned_operator_prediction": learned["learned_operator_prediction"],
            "observed_reject_proxy": learned["observed_reject_proxy"],
            "raw_interaction_absolute_error": raw_error,
            "learned_operator_absolute_error": learned_error,
            "non_regression_vs_raw_interaction": learned_error <= raw_error,
            "raw_interaction_false_alarm": learned["raw_interaction_false_alarm"],
            "learned_operator_false_alarm": learned["learned_operator_false_alarm"],
            "false_alarm_reduced": (
                learned["raw_interaction_false_alarm"]
                and not learned["learned_operator_false_alarm"]
            ),
            "static_prior_missed_high_risk": learned[
                "static_prior_missed_high_risk"
            ],
            "static_prior_miss_recovered": (
                not learned["static_prior_missed_high_risk"]
                or learned["learned_operator_flags_new_risk"]
            ),
            "transfer_diagnostics": learned["transfer_diagnostics"],
        }
        trials.append(return_trial)
    return trials


def _summary(trials: list[dict[str, Any]]) -> dict[str, Any]:
    false_alarm_trials = [
        trial for trial in trials if trial["raw_interaction_false_alarm"]
    ]
    static_miss_trials = [
        trial for trial in trials if trial["static_prior_missed_high_risk"]
    ]
    return {
        "holdout_trial_count": len(trials),
        "non_regression_rate": _rate(
            sum(1 for trial in trials if trial["non_regression_vs_raw_interaction"]),
            len(trials),
        ),
        "false_alarm_reduction_rate": _rate(
            sum(1 for trial in false_alarm_trials if trial["false_alarm_reduced"]),
            len(false_alarm_trials),
        ),
        "static_prior_miss_recovery_rate": _rate(
            sum(
                1
                for trial in static_miss_trials
                if trial["static_prior_miss_recovered"]
            ),
            len(static_miss_trials),
        ),
        "mean_error_reduction_vs_raw_interaction": round(
            sum(
                trial["raw_interaction_absolute_error"]
                - trial["learned_operator_absolute_error"]
                for trial in trials
            )
            / len(trials),
            3,
        ),
    }


def _stress_grid(case_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grid = []
    for floor in [0.0, 0.35, UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR, 1.0]:
        for calibration in [False, True]:
            summary = _summary(
                _variant_trials(
                    case_results=case_results,
                    unknown_mechanism_weight=floor,
                    risk_preserving_calibration_enabled=calibration,
                )
            )
            grid.append(
                {
                    "unknown_mechanism_weight": floor,
                    "risk_preserving_calibration_enabled": calibration,
                    "summary": summary,
                    "passes_current_proxy_holdout_gate": (
                        _summary_passes_holdout_gate(summary)
                    ),
                }
            )
    return grid


def _component_contribution(*, variant_id: str, summary: dict[str, Any]) -> list[str]:
    if variant_id == "learned_weights_only":
        return ["learned_weights_alone_do_not_recover_unseen_static_prior_miss"]
    if variant_id == "unseen_floor_only":
        return ["unseen_mechanism_floor_recovers_static_prior_miss_signal"]
    if variant_id == SELECTED_VARIANT_ID:
        contributions = [
            "unseen_mechanism_floor_recovers_static_prior_miss_signal",
            "risk_preserving_calibration_restores_non_regression",
        ]
        if summary["false_alarm_reduction_rate"] >= 0.80:
            contributions.append("false_alarm_reduction_preserved")
        return contributions
    return []


def _variant_by_id(
    variants: list[dict[str, Any]],
    variant_id: str,
) -> dict[str, Any]:
    for variant in variants:
        if variant["variant_id"] == variant_id:
            return variant
    raise ValueError(f"unknown variant_id: {variant_id}")


def _passes_holdout_gate(variant: dict[str, Any]) -> bool:
    return _summary_passes_holdout_gate(variant["summary"])


def _summary_passes_holdout_gate(summary: dict[str, Any]) -> bool:
    return (
        summary["non_regression_rate"] >= 0.80
        and summary["false_alarm_reduction_rate"] >= 0.80
        and summary["static_prior_miss_recovery_rate"] >= 0.80
    )


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_counterfactual_calibration_ablation(
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
