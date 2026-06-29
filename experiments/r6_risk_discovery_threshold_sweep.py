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
    finite_number,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics


R6_RISK_DISCOVERY_THRESHOLD_SWEEP_SCHEMA_VERSION = (
    "r6-risk-discovery-threshold-sweep-v1"
)
DEFAULT_INTERACTION_DELTA_THRESHOLDS = [
    0.0,
    0.01,
    0.02,
    0.03,
    0.04,
    0.05,
    0.06,
    0.07,
    0.08,
    0.09,
    0.10,
]


def build_r6_risk_discovery_threshold_sweep(
    *,
    artifact_id: str,
    run_id: str,
    interaction_delta_thresholds: list[float] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    thresholds = _normalize_thresholds(
        interaction_delta_thresholds or DEFAULT_INTERACTION_DELTA_THRESHOLDS
    )
    threshold_results = [
        _threshold_result(
            artifact_id=artifact_id,
            run_id=run_id,
            threshold=threshold,
        )
        for threshold in thresholds
    ]
    summary = _summary(threshold_results)
    passing_threshold_found = summary["passing_threshold_count"] > 0
    separating_threshold_found = summary["separating_threshold_found"]
    status = (
        "threshold_sweep_found_candidate_rule"
        if passing_threshold_found
        else (
            "threshold_sweep_no_separating_rule"
            if summary["true_signal_false_alarm_delta_overlap"]
            else "threshold_sweep_no_passing_threshold"
        )
    )
    report = {
        "schema_version": R6_RISK_DISCOVERY_THRESHOLD_SWEEP_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "sweep_definition": {
            "interaction_delta_thresholds": thresholds,
            "high_risk_threshold": 0.40,
            "static_miss_threshold": 0.05,
            "purpose": (
                "Test whether threshold tuning alone can reduce false alarms "
                "while preserving static-prior miss recovery."
            ),
        },
        "summary": summary,
        "threshold_results": threshold_results,
        "acceptance_gates": {
            "threshold_sweep_present": True,
            "passing_threshold_found": passing_threshold_found,
            "separating_threshold_found": separating_threshold_found,
            "false_alarm_reducible_by_threshold": summary[
                "false_alarm_reducible_by_threshold"
            ],
            "true_signal_false_alarm_delta_overlap": summary[
                "true_signal_false_alarm_delta_overlap"
            ],
        },
        "decision": {
            "threshold_tuning_sufficient": passing_threshold_found,
            "decision": (
                "threshold_candidate_available"
                if passing_threshold_found
                else "needs_non_threshold_false_alarm_discriminator"
            ),
            "recommended_next_step": (
                "validate_threshold_on_same_family_holdout"
                if passing_threshold_found
                else "add_case_level_features_or_in_condition_holdout_before_threshold_tuning"
            ),
        },
        "source_refs": [
            result["decision_value_metrics_artifact_id"]
            for result in threshold_results
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            (
                "Threshold sweep diagnoses whether rule tuning can reduce false "
                "alarms; it is not field validation."
            ),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": _risk_flags(summary),
        "blocking_gaps": [] if passing_threshold_found else [
            "needs_non_threshold_false_alarm_discriminator",
            "needs_risk_discovery_holdout_validation",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_risk_discovery_threshold_sweep(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r6_risk_discovery_threshold_sweep(**kwargs),
    )


def _normalize_thresholds(values: list[float]) -> list[float]:
    thresholds = []
    for index, value in enumerate(values):
        threshold = finite_number(value, field=f"interaction_delta_thresholds[{index}]")
        if threshold < 0:
            raise ValueError("interaction_delta_threshold must be non-negative")
        rounded = round(threshold, 3)
        if rounded not in thresholds:
            thresholds.append(rounded)
    if not thresholds:
        raise ValueError("interaction_delta_thresholds must not be empty")
    return sorted(thresholds)


def _threshold_result(
    *,
    artifact_id: str,
    run_id: str,
    threshold: float,
) -> dict[str, Any]:
    metrics = build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-threshold-{_threshold_id(threshold)}",
        run_id=run_id,
        interaction_delta_threshold=threshold,
    )
    summary = metrics["summary"]
    case_results = [
        {
            "source_key": case["source_key"],
            "interaction_delta_vs_static": case["interaction_delta_vs_static"],
            "observed_high_risk": case["observed_high_risk"],
            "interaction_flags_new_risk": case["interaction_flags_new_risk"],
            "interaction_false_alarm": case["interaction_false_alarm"],
            "recovered_static_prior_miss": case["recovered_static_prior_miss"],
        }
        for case in metrics["case_results"]
    ]
    return {
        "threshold": threshold,
        "decision_value_metrics_artifact_id": metrics["artifact_id"],
        "status": metrics["status"],
        "decision_value_passed": metrics["decision_value_passed"],
        "risk_utility_score": _risk_utility_score(summary),
        "summary": summary,
        "case_results": case_results,
    }


def _threshold_id(threshold: float) -> str:
    return f"{threshold:.3f}".replace(".", "p")


def _risk_utility_score(summary: dict[str, Any]) -> float:
    return round(
        summary["decision_regret_reduction"]
        + summary["static_prior_miss_recovery_rate"]
        + summary["top_k_risk_hit_rate"]
        - summary["false_alarm_rate"],
        3,
    )


def _summary(threshold_results: list[dict[str, Any]]) -> dict[str, Any]:
    passing_results = [
        result for result in threshold_results if result["decision_value_passed"]
    ]
    best_result = max(
        threshold_results,
        key=lambda result: (
            result["decision_value_passed"],
            result["risk_utility_score"],
            result["summary"]["decision_regret_reduction"],
            result["summary"]["static_prior_miss_recovery_rate"],
            result["summary"]["top_k_risk_hit_rate"],
            -result["summary"]["false_alarm_rate"],
            -result["threshold"],
        ),
    )
    true_positive_deltas = _case_delta_values(
        threshold_results,
        predicate=lambda case: case["recovered_static_prior_miss"],
    )
    false_alarm_deltas = _case_delta_values(
        threshold_results,
        predicate=lambda case: case["interaction_false_alarm"],
    )
    overlap = sorted(set(true_positive_deltas) & set(false_alarm_deltas))
    false_alarm_reducible = any(
        result["summary"]["static_prior_miss_recovery_rate"] >= 0.80
        and result["summary"]["false_alarm_rate"] <= 0.50
        and result["summary"]["decision_regret_reduction"] > 0
        for result in threshold_results
    )
    return {
        "threshold_count": len(threshold_results),
        "passing_threshold_count": len(passing_results),
        "separating_threshold_found": bool(passing_results),
        "false_alarm_reducible_by_threshold": false_alarm_reducible,
        "best_threshold": best_result["threshold"],
        "best_threshold_status": best_result["status"],
        "best_threshold_score": best_result["risk_utility_score"],
        "unique_interaction_delta_values": _case_delta_values(
            threshold_results,
            predicate=lambda case: True,
        ),
        "true_positive_delta_values": true_positive_deltas,
        "false_alarm_delta_values": false_alarm_deltas,
        "true_signal_false_alarm_delta_overlap": bool(overlap),
    }


def _case_delta_values(
    threshold_results: list[dict[str, Any]],
    *,
    predicate: Any,
) -> list[float]:
    values = []
    for result in threshold_results:
        for case in result["case_results"]:
            if predicate(case):
                value = case["interaction_delta_vs_static"]
                if value not in values:
                    values.append(value)
    return sorted(values)


def _risk_flags(summary: dict[str, Any]) -> list[str]:
    flags = ["threshold_sweep_not_field_validation"]
    if not summary["passing_threshold_count"]:
        flags.append("threshold_tuning_cannot_resolve_current_false_alarms")
    if summary["true_signal_false_alarm_delta_overlap"]:
        flags.append("true_signal_and_false_alarm_share_same_delta")
    return flags


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--interaction-delta-threshold",
        action="append",
        type=float,
        dest="interaction_delta_thresholds",
    )
    args = parser.parse_args()

    output_path = write_r6_risk_discovery_threshold_sweep(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        interaction_delta_thresholds=args.interaction_delta_thresholds,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output_path),
                "passing_threshold_found": report["acceptance_gates"][
                    "passing_threshold_found"
                ],
                "status": report["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
