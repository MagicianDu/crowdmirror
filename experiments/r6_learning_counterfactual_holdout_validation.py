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
from experiments.r6_learning_counterfactual_simulator import (
    _case_result,
    _learn_mechanism_weights,
    build_r6_learning_counterfactual_simulator,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_LEARNING_COUNTERFACTUAL_HOLDOUT_VALIDATION_SCHEMA_VERSION = (
    "r6-learning-counterfactual-holdout-validation-v1"
)
UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR = 0.65


def build_r6_learning_counterfactual_holdout_validation(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    learning_counterfactual_simulator: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id=f"{artifact_id}-trend-interval-risk",
        run_id=run_id,
    )
    simulator = (
        learning_counterfactual_simulator
        or build_r6_learning_counterfactual_simulator(
            artifact_id=f"{artifact_id}-learning-counterfactual-simulator",
            run_id=run_id,
            trend_interval_risk_metrics=metrics,
        )
    )
    trials = _leave_one_case_trials(metrics["case_results"])
    summary = _summary(trials)
    independent_holdout_passed = (
        summary["non_regression_rate"] >= 0.80
        and summary["false_alarm_reduction_rate"] >= 0.80
        and summary["static_prior_miss_recovery_rate"] >= 0.80
        and summary["diagnostic_blocked_count"] == 0
    )
    report = {
        "schema_version": R6_LEARNING_COUNTERFACTUAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "learning_counterfactual_holdout_passed_guarded"
            if independent_holdout_passed
            else "learning_counterfactual_holdout_mixed_blocked"
        ),
        "claim_status": "guarded_supported"
        if independent_holdout_passed
        else "diagnostic_blocked",
        "validation_protocol": {
            "protocol_id": "leave_one_case_mechanism_weight_transfer",
            "train_unit": "all current proxy cases except heldout_source_key",
            "heldout_unit": "one current proxy case",
            "unseen_mechanism_transfer_floor": (
                UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR
            ),
            "field_outcome_required_for_runtime_default": True,
        },
        "summary": summary,
        "holdout_trials": trials,
        "acceptance_gates": {
            "leave_one_case_holdout_present": bool(trials),
            "non_regression_rate_passed": summary["non_regression_rate"] >= 0.80,
            "false_alarm_reduction_rate_passed": (
                summary["false_alarm_reduction_rate"] >= 0.80
            ),
            "static_prior_miss_recovery_preserved": (
                summary["static_prior_miss_recovery_rate"] >= 0.80
            ),
            "independent_holdout_passed": independent_holdout_passed,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            metrics["artifact_id"],
            simulator["artifact_id"],
            *[
                source_ref
                for trial in trials
                for source_ref in trial["source_artifact_ids"]
            ],
        ],
        "allowed_claims": [
            "Learning counterfactual simulator has explicit leave-one-case holdout evidence.",
            "Mixed holdout evidence can be shown as diagnostic support for Product policy comparison.",
        ],
        "blocked_claims": [
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "learned mechanism weights are independently validated",
            "learned operator can be enabled by default",
        ],
        "blocking_gaps": _blocking_gaps(independent_holdout_passed),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_learning_counterfactual_holdout_validation(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_learning_counterfactual_holdout_validation(**kwargs),
    )


def _leave_one_case_trials(
    case_results: list[dict[str, Any]],
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
            unknown_mechanism_weight=UNKNOWN_HIGH_RISK_MECHANISM_TRANSFER_FLOOR,
        )
        learned = _apply_risk_preserving_calibration(learned)
        raw_error = round(
            abs(learned["raw_interaction_prediction"] - learned["observed_reject_proxy"]),
            3,
        )
        learned_error = round(
            abs(learned["learned_operator_prediction"] - learned["observed_reject_proxy"]),
            3,
        )
        non_regression = learned_error <= raw_error
        false_alarm_reduced = (
            learned["raw_interaction_false_alarm"]
            and not learned["learned_operator_false_alarm"]
        )
        static_miss_recovered = (
            not learned["static_prior_missed_high_risk"]
            or learned["learned_operator_flags_new_risk"]
        )
        supported = non_regression and (
            false_alarm_reduced or static_miss_recovered
        )
        trials.append(
            {
                "heldout_source_key": heldout["source_key"],
                "heldout_target_case_id": heldout["target_case_id"],
                "train_source_keys": [case["source_key"] for case in train_cases],
                "learned_mechanism_weights": sorted(
                    weights.values(),
                    key=lambda item: item["mechanism_id"],
                ),
                "raw_interaction_prediction": learned["raw_interaction_prediction"],
                "learned_operator_prediction": learned["learned_operator_prediction"],
                "observed_reject_proxy": learned["observed_reject_proxy"],
                "raw_interaction_absolute_error": raw_error,
                "learned_operator_absolute_error": learned_error,
                "non_regression_vs_raw_interaction": non_regression,
                "raw_interaction_false_alarm": learned["raw_interaction_false_alarm"],
                "learned_operator_false_alarm": learned["learned_operator_false_alarm"],
                "false_alarm_reduced": false_alarm_reduced,
                "learned_operator_flags_new_risk": learned[
                    "learned_operator_flags_new_risk"
                ],
                "static_prior_missed_high_risk": learned[
                    "static_prior_missed_high_risk"
                ],
                "static_prior_miss_recovered": static_miss_recovered,
                "transfer_diagnostics": learned["transfer_diagnostics"],
                "claim_status": "guarded_supported"
                if supported
                else "diagnostic_blocked",
                "source_artifact_ids": learned["source_artifact_ids"],
            }
        )
    return trials


def _apply_risk_preserving_calibration(
    learned: dict[str, Any],
) -> dict[str, Any]:
    calibrated = dict(learned)
    diagnostics = dict(calibrated["transfer_diagnostics"])
    reasons = list(diagnostics["diagnostic_reasons"])
    should_calibrate = (
        calibrated["static_prior_missed_high_risk"]
        and calibrated["learned_operator_flags_new_risk"]
        and calibrated["learned_operator_prediction"]
        < calibrated["raw_interaction_prediction"]
    )
    if not should_calibrate:
        diagnostics["risk_preserving_calibration_applied"] = False
        calibrated["transfer_diagnostics"] = diagnostics
        return calibrated

    calibrated["learned_operator_prediction"] = calibrated[
        "raw_interaction_prediction"
    ]
    calibrated["learned_operator_delta"] = round(
        calibrated["learned_operator_prediction"]
        - calibrated["static_prior_prediction"],
        3,
    )
    if "calibrated_to_raw_interaction_for_static_miss_recovery" not in reasons:
        reasons.append("calibrated_to_raw_interaction_for_static_miss_recovery")
    diagnostics["diagnostic_reasons"] = reasons
    diagnostics["risk_preserving_calibration_applied"] = True
    diagnostics["risk_preserving_calibration_target"] = "raw_interaction_prediction"
    calibrated["transfer_diagnostics"] = diagnostics
    return calibrated


def _summary(trials: list[dict[str, Any]]) -> dict[str, Any]:
    false_alarm_trials = [
        trial for trial in trials if trial["raw_interaction_false_alarm"]
    ]
    static_miss_trials = [
        trial for trial in trials if trial["static_prior_missed_high_risk"]
    ]
    supported = [
        trial for trial in trials if trial["claim_status"] == "guarded_supported"
    ]
    return {
        "holdout_trial_count": len(trials),
        "supported_holdout_count": len(supported),
        "diagnostic_blocked_count": len(trials) - len(supported),
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


def _blocking_gaps(independent_holdout_passed: bool) -> list[str]:
    gaps = [
        "needs_field_or_customer_outcome_validation",
        "needs_runtime_default_guard_review",
    ]
    if not independent_holdout_passed:
        gaps.insert(0, "needs_more_independent_holdout_support")
    return gaps


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

    output_path = write_r6_learning_counterfactual_holdout_validation(
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
