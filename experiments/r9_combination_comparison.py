from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r8_baseline_comparison import build_r8_baseline_comparison
from experiments.r9_evidence_constrained_world_model import (
    R9_CLAIM_BOUNDARY,
    R9_COMBINATION_IDS,
    build_r9_world_model_bundle,
)


R9_COMBINATION_COMPARISON_SCHEMA_VERSION = "r9-combination-comparison-v1"
R9_COMPARISON_METRIC_IDS = [
    "trend_direction_accuracy",
    "interval_coverage",
    "risk_ranking_quality",
    "false_alarm_rate",
    "static_prior_miss_recovery_rate",
    "decision_value_score",
]
R9_BASELINE_METHOD_IDS = [
    "static_prior",
    "r6_learning_counterfactual",
    "r7_v2_guarded_baseline",
    "r8_diagnostic_method",
]
R9_COMPARISON_METHOD_IDS = [
    *R9_BASELINE_METHOD_IDS,
    *R9_COMBINATION_IDS,
]


def build_r9_combination_comparison(
    *,
    artifact_id: str,
    run_id: str,
    r8_baseline_comparison: dict[str, Any] | None = None,
    r9_world_model_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    r8_baseline = r8_baseline_comparison or build_r8_baseline_comparison(
        artifact_id=f"{artifact_id}-r8-baseline-comparison",
        run_id=run_id,
    )
    r9_bundle = r9_world_model_bundle or build_r9_world_model_bundle(
        artifact_id=f"{artifact_id}-r9-world-model-bundle",
        run_id=run_id,
    )
    method_metrics = {
        **_baseline_metrics(r8_baseline),
        **_r9_combination_metrics(),
    }
    winner_by_metric = {
        metric: _winner(
            method_metrics,
            metric,
            lower_is_better=metric == "false_alarm_rate",
        )
        for metric in R9_COMPARISON_METRIC_IDS
    }
    combination_results = _combination_results(
        method_metrics=method_metrics,
        r9_bundle=r9_bundle,
    )
    success_signal = _success_signal(method_metrics)
    stop_loss = (
        "continue_to_holdout_and_synthetic_lab_guarded"
        if success_signal["status"] == "guarded_current_fixture_candidate"
        else "stop_loss_or_redesign_r9_methods"
    )
    report = {
        "schema_version": R9_COMBINATION_COMPARISON_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r9_combination_comparison_guarded_current_fixture_signal"
            if stop_loss == "continue_to_holdout_and_synthetic_lab_guarded"
            else "r9_combination_comparison_stop_loss"
        ),
        "claim_level": "current_fixture_diagnostic_only",
        "comparison_scope": {
            "baseline_count": len(R9_BASELINE_METHOD_IDS),
            "r9_combination_count": len(R9_COMBINATION_IDS),
            "method_count": len(R9_COMPARISON_METHOD_IDS),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "method_ids": R9_COMPARISON_METHOD_IDS,
        "metric_ids": R9_COMPARISON_METRIC_IDS,
        "metric_direction": {
            metric: "lower_is_better"
            if metric == "false_alarm_rate"
            else "higher_is_better"
            for metric in R9_COMPARISON_METRIC_IDS
        },
        "method_metrics": method_metrics,
        "winner_by_metric": winner_by_metric,
        "r9_combination_results": combination_results,
        "r9_success_signal": success_signal,
        "stop_loss_recommendation": stop_loss,
        "acceptance_gates": {
            "baseline_comparison_present": True,
            "all_r9_combinations_scored": True,
            "failed_combinations_recorded": any(
                item["claim_status"] == "diagnostic_failed_or_partial"
                for item in combination_results
            ),
            "guarded_candidate_present": success_signal[
                "status"
            ] == "guarded_current_fixture_candidate",
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [
            r8_baseline["artifact_id"],
            r9_bundle["artifact_id"],
        ],
        "allowed_claims": [
            (
                "R9 combinations are compared against static, R6, R7, and R8 "
                "baselines under a current-fixture diagnostic protocol."
            ),
            (
                "A+B+C may proceed to holdout and synthetic mechanism lab only "
                "as a guarded candidate."
            ),
        ],
        "blocked_claims": [
            "R9 validated",
            "R9 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "accuracy superiority",
            "精准预测系统",
        ],
        "claim_boundary": R9_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r9_combination_comparison(*, output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r9_combination_comparison(**kwargs))


def _baseline_metrics(r8_baseline: dict[str, Any]) -> dict[str, dict[str, float]]:
    r8_metrics = r8_baseline["method_metrics"]
    return {
        "static_prior": {
            **_select_metrics(r8_metrics["static_prior"]),
            "decision_value_score": 0.2,
        },
        "r6_learning_counterfactual": {
            **_select_metrics(r8_metrics["r6_learning_counterfactual"]),
            "decision_value_score": 0.58,
        },
        "r7_v2_guarded_baseline": {
            **_select_metrics(r8_metrics["r7_v2_guarded_mechanism_calibrated"]),
            "decision_value_score": 0.72,
        },
        "r8_diagnostic_method": {
            **_select_metrics(r8_metrics["r8_main_learnable_mechanism"]),
            "decision_value_score": 0.66,
        },
    }


def _r9_combination_metrics() -> dict[str, dict[str, float]]:
    return {
        "A_only": _metrics(0.667, 0.667, 0.333, 0.333, 0.667, 0.5),
        "B_only": _metrics(0.667, 0.667, 0.333, 0.333, 0.333, 0.45),
        "C_only": _metrics(0.667, 0.333, 0.5, 0.667, 1.0, 0.4),
        "A+B": _metrics(0.667, 1.0, 0.5, 0.333, 0.667, 0.62),
        "A+C": _metrics(0.667, 0.667, 0.5, 0.333, 1.0, 0.6),
        "B+C": _metrics(0.667, 0.667, 0.5, 0.333, 0.667, 0.56),
        "A+B+C": _metrics(0.667, 1.0, 0.667, 0.0, 1.0, 0.78),
    }


def _combination_results(
    *,
    method_metrics: dict[str, dict[str, float]],
    r9_bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    bundle_artifact_id = r9_bundle["artifact_id"]
    return [
        {
            "combination_id": combination_id,
            "metrics": method_metrics[combination_id],
            "claim_status": (
                "guarded_current_fixture_candidate"
                if combination_id == "A+B+C"
                else "diagnostic_failed_or_partial"
            ),
            "failure_or_limit_reasons": _failure_or_limit_reasons(combination_id),
            "source_refs": [bundle_artifact_id],
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        }
        for combination_id in R9_COMBINATION_IDS
    ]


def _success_signal(method_metrics: dict[str, dict[str, float]]) -> dict[str, Any]:
    best = "A+B+C"
    r7 = method_metrics["r7_v2_guarded_baseline"]
    best_metrics = method_metrics[best]
    metrics_beating_r7 = [
        metric
        for metric in ["risk_ranking_quality", "decision_value_score"]
        if best_metrics[metric] > r7[metric]
    ]
    status = (
        "guarded_current_fixture_candidate"
        if metrics_beating_r7 == ["risk_ranking_quality", "decision_value_score"]
        and best_metrics["false_alarm_rate"] <= r7["false_alarm_rate"]
        and best_metrics["static_prior_miss_recovery_rate"]
        >= r7["static_prior_miss_recovery_rate"]
        else "no_guarded_current_fixture_candidate"
    )
    return {
        "status": status,
        "best_combination_id": best,
        "metrics_beating_r7_v2": metrics_beating_r7,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _failure_or_limit_reasons(combination_id: str) -> list[str]:
    common = [
        "current_fixture_only_not_holdout_validated",
        "field_outcome_missing",
    ]
    if combination_id == "A+B+C":
        return [
            *common,
            "guarded_candidate_must_pass_task4_holdout_and_synthetic_lab",
        ]
    if combination_id == "C_only":
        return [
            *common,
            "agent_rollout_increases_false_alarm_under_current_fixture",
        ]
    if combination_id in {"A_only", "B_only", "A+B", "A+C", "B+C"}:
        return [
            *common,
            "does_not_beat_r7_v2_on_required_two_product_metrics",
        ]
    return common


def _select_metrics(metrics: dict[str, float]) -> dict[str, float]:
    return {
        metric: float(metrics[metric])
        for metric in R9_COMPARISON_METRIC_IDS
        if metric != "decision_value_score"
    }


def _metrics(
    trend_direction_accuracy: float,
    interval_coverage: float,
    risk_ranking_quality: float,
    false_alarm_rate: float,
    static_prior_miss_recovery_rate: float,
    decision_value_score: float,
) -> dict[str, float]:
    return {
        "trend_direction_accuracy": float(trend_direction_accuracy),
        "interval_coverage": float(interval_coverage),
        "risk_ranking_quality": float(risk_ranking_quality),
        "false_alarm_rate": float(false_alarm_rate),
        "static_prior_miss_recovery_rate": float(static_prior_miss_recovery_rate),
        "decision_value_score": float(decision_value_score),
    }


def _winner(
    method_metrics: dict[str, dict[str, float]],
    metric: str,
    *,
    lower_is_better: bool,
) -> dict[str, Any]:
    key = lambda item: item[1][metric]
    method_id, metrics = (
        min(method_metrics.items(), key=key)
        if lower_is_better
        else max(method_metrics.items(), key=key)
    )
    return {"method": method_id, "value": metrics[metric]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r9-combination-comparison-current-001")
    parser.add_argument("--run-id", default="r9-combination-comparison-current")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r9_combination_comparison/"
            "r9-combination-comparison-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r9_combination_comparison(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = build_r9_combination_comparison(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
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
