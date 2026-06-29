from __future__ import annotations

import argparse
import copy
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
from experiments.r6_counterfactual_calibration_ablation import (
    _summary_passes_holdout_gate,
    _variant_trials,
)
from experiments.r6_learning_counterfactual_holdout_validation import (
    UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_COUNTERFACTUAL_ROBUSTNESS_VALIDATION_SCHEMA_VERSION = (
    "r6-counterfactual-robustness-validation-v1"
)
PERTURBATION_DELTAS = [-0.03, 0.0, 0.03]


def build_r6_counterfactual_robustness_validation(
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
    scenarios = _perturbation_scenarios(metrics["case_results"])
    summary = _summary(scenarios)
    passed = summary["robustness_pass_rate"] >= 1.0
    report = {
        "schema_version": R6_COUNTERFACTUAL_ROBUSTNESS_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "counterfactual_robustness_current_proxy_passed_guarded"
        if passed
        else "counterfactual_robustness_diagnostic_blocked",
        "claim_status": "guarded" if passed else "diagnostic",
        "robustness_protocol": {
            "protocol_id": "local_proxy_outcome_perturbation",
            "perturbation_deltas": PERTURBATION_DELTAS,
            "selected_variant_id": "floor_plus_non_regression_calibration",
            "unknown_mechanism_weight": UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR,
            "risk_preserving_calibration_enabled": True,
            "field_outcome_required_for_runtime_default": True,
        },
        "summary": summary,
        "perturbation_scenarios": scenarios,
        "acceptance_gates": {
            "perturbation_scenarios_present": bool(scenarios),
            "local_proxy_robustness_passed": passed,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [metrics["artifact_id"]],
        "allowed_claims": [
            "Selected counterfactual calibration is robust to small current-proxy outcome perturbations.",
            "Robustness validation can be shown as guarded diagnostic evidence only.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "robustness under real customer outcome drift is proven",
        ],
        "blocking_gaps": [
            "needs_field_or_customer_outcome_validation",
            "needs_external_outcome_robustness_validation",
            "needs_near_threshold_false_alarm_calibration",
            "needs_runtime_default_guard_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_counterfactual_robustness_validation(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_counterfactual_robustness_validation(**kwargs),
    )


def _perturbation_scenarios(
    case_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scenarios = []
    for source_key in [case["source_key"] for case in case_results]:
        for delta in PERTURBATION_DELTAS:
            perturbed_cases = _perturb_case_results(
                case_results,
                source_key=source_key,
                delta=delta,
            )
            trials = _variant_trials(
                case_results=perturbed_cases,
                unknown_mechanism_weight=UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR,
                risk_preserving_calibration_enabled=True,
            )
            summary = _scenario_summary(trials)
            scenarios.append(
                {
                    "scenario_id": f"{source_key}:{delta:+.2f}",
                    "perturbed_source_key": source_key,
                    "perturbation_delta": round(delta, 2),
                    "summary": summary,
                    "passes_current_proxy_holdout_gate": (
                        _summary_passes_holdout_gate(summary)
                    ),
                    "holdout_trials": trials,
                }
            )
    return scenarios


def _perturb_case_results(
    case_results: list[dict[str, Any]],
    *,
    source_key: str,
    delta: float,
) -> list[dict[str, Any]]:
    perturbed = copy.deepcopy(case_results)
    for case in perturbed:
        if case["source_key"] != source_key:
            continue
        observed = round(
            max(0.0, min(1.0, float(case["observed_reject_proxy"]) + delta)),
            3,
        )
        case["observed_reject_proxy"] = observed
        case["outcome_direction"] = _direction(observed - case["static_prior_prediction"])
        case["trend_direction_matches_outcome"] = (
            case["trend_direction"] == case["outcome_direction"]
        )
        case["risk_interval"]["contains_observed"] = (
            case["risk_interval"]["lower"]
            <= observed
            <= case["risk_interval"]["upper"]
        )
        case["interaction_false_alarm"] = (
            case["interaction_prediction"] - case["static_prior_prediction"] >= 0.03
            and observed < 0.40
        )
        case["risk_ranking_hit"] = (
            case["interaction_prediction"] - case["static_prior_prediction"] >= 0.03
            and observed >= 0.40
        )
    return perturbed


def _scenario_summary(trials: list[dict[str, Any]]) -> dict[str, Any]:
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


def _summary(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "perturbation_scenario_count": len(scenarios),
        "passed_scenario_count": sum(
            1 for scenario in scenarios if scenario["passes_current_proxy_holdout_gate"]
        ),
        "robustness_pass_rate": _rate(
            sum(
                1
                for scenario in scenarios
                if scenario["passes_current_proxy_holdout_gate"]
            ),
            len(scenarios),
        ),
        "min_non_regression_rate": min(
            scenario["summary"]["non_regression_rate"] for scenario in scenarios
        ),
        "min_false_alarm_reduction_rate": min(
            scenario["summary"]["false_alarm_reduction_rate"] for scenario in scenarios
        ),
        "min_static_prior_miss_recovery_rate": min(
            scenario["summary"]["static_prior_miss_recovery_rate"] for scenario in scenarios
        ),
    }


def _direction(delta: float) -> str:
    if delta > 0:
        return "risk_up"
    if delta < 0:
        return "risk_down"
    return "flat"


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_counterfactual_robustness_validation(
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
