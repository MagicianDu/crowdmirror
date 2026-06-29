from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_DECISION_VALUE_METRICS_SCHEMA_VERSION = "r6-decision-value-metrics-v1"
DEFAULT_SOURCE_KEYS = [
    "htops_cost_pressure",
    "anes_health_heldout",
    "anes_climate_heldout",
]


def build_r6_decision_value_metrics(
    *,
    artifact_id: str,
    run_id: str,
    ablation_reports: list[dict[str, Any]] | None = None,
    source_keys: list[str] | None = None,
    high_risk_threshold: float = 0.40,
    interaction_delta_threshold: float = 0.03,
    static_miss_threshold: float = 0.05,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    reports = ablation_reports or _build_default_ablation_reports(
        artifact_id=artifact_id,
        run_id=run_id,
        source_keys=source_keys or DEFAULT_SOURCE_KEYS,
    )
    case_results = [
        _case_decision_value(
            report,
            high_risk_threshold=high_risk_threshold,
            interaction_delta_threshold=interaction_delta_threshold,
            static_miss_threshold=static_miss_threshold,
        )
        for report in reports
    ]
    summary = _summary(case_results)
    passed = (
        summary["static_prior_miss_recovery_rate"] >= 0.80
        and summary["top_k_risk_hit_rate"] >= 0.50
        and summary["false_alarm_rate"] <= 0.50
        and summary["decision_regret_reduction"] > 0
    )
    status = "decision_value_passed" if passed else "decision_value_partial_high_false_alarm"
    report = {
        "schema_version": R6_DECISION_VALUE_METRICS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "metric_definition": {
            "high_risk_threshold": high_risk_threshold,
            "interaction_delta_threshold": interaction_delta_threshold,
            "static_miss_threshold": static_miss_threshold,
            "top_k_risk_hit_rate": (
                "Share of interaction-flagged new-risk cases whose observed reject "
                "proxy is high risk."
            ),
            "static_prior_miss_recovery_rate": (
                "Share of cases where static prior missed high risk and interaction "
                "flagged the risk before outcome evaluation."
            ),
            "decision_regret_reduction": (
                "Reduction in missed high-risk cases when using interaction flags "
                "instead of static-prior high-risk flags."
            ),
        },
        "decision_value_passed": passed,
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": {
            "decision_value_metric_present": True,
            "static_prior_miss_recovery_observed": (
                summary["static_prior_miss_recovered_count"] > 0
            ),
            "top_k_risk_hit_rate_passed": summary["top_k_risk_hit_rate"] >= 0.50,
            "false_alarm_rate_passed": summary["false_alarm_rate"] <= 0.50,
            "decision_regret_reduction_positive": (
                summary["decision_regret_reduction"] > 0
            ),
            "decision_value_passed": passed,
        },
        "source_refs": [report["artifact_id"] for report in reports],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Decision-value metrics evaluate risk discovery utility, not aggregate accuracy superiority.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "decision_value_not_field_validation",
            "current_public_proxies_have_high_false_alarm_rate",
        ],
        "blocking_gaps": [] if passed else [
            "needs_lower_false_alarm_rate",
            "needs_risk_discovery_holdout_validation",
            "needs_field_outcome_validation",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_decision_value_metrics(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_decision_value_metrics(**kwargs))


def _build_default_ablation_reports(
    *,
    artifact_id: str,
    run_id: str,
    source_keys: list[str],
) -> list[dict[str, Any]]:
    reports = []
    for source_key in source_keys:
        proxy = build_r6_public_outcome_proxy(
            artifact_id=f"{artifact_id}-{source_key}-proxy",
            run_id=run_id,
            source_key=source_key,
        )
        reports.append(
            build_r6_ablation_report(
                artifact_id=f"{artifact_id}-{source_key}-ablation",
                run_id=run_id,
                public_outcome_proxy=proxy,
            )
        )
    return reports


def _case_decision_value(
    ablation: dict[str, Any],
    *,
    high_risk_threshold: float,
    interaction_delta_threshold: float,
    static_miss_threshold: float,
) -> dict[str, Any]:
    by_method = {result["method"]: result for result in ablation["baseline_results"]}
    static = by_method["no_interaction_prior"]
    interaction = by_method["prior_anchored_interaction"]
    random_noise = by_method["random_noise_baseline"]
    static_prediction = float(static["mean_prediction"])
    interaction_prediction = float(interaction["mean_prediction"])
    observed = float(interaction["observed_reject_proxy"])
    interaction_delta = round(interaction_prediction - static_prediction, 3)
    observed_high_risk = observed >= high_risk_threshold
    static_prior_flags_high_risk = static_prediction >= high_risk_threshold
    interaction_flags_new_risk = interaction_delta >= interaction_delta_threshold
    static_prior_missed_high_risk = (
        observed_high_risk
        and not static_prior_flags_high_risk
        and observed - static_prediction >= static_miss_threshold
    )
    recovered_static_prior_miss = (
        static_prior_missed_high_risk and interaction_flags_new_risk
    )
    interaction_false_alarm = interaction_flags_new_risk and not observed_high_risk
    return {
        "artifact_id": ablation["artifact_id"],
        "source_key": _source_key(ablation),
        "target_case_id": ablation["target_case_id"],
        "static_prior_prediction": round(static_prediction, 3),
        "interaction_prediction": round(interaction_prediction, 3),
        "random_noise_prediction": round(float(random_noise["mean_prediction"]), 3),
        "observed_reject_proxy": round(observed, 3),
        "interaction_delta_vs_static": interaction_delta,
        "observed_minus_static_prior": round(observed - static_prediction, 3),
        "static_absolute_error": static["mean_absolute_error"],
        "interaction_absolute_error": interaction["mean_absolute_error"],
        "observed_high_risk": observed_high_risk,
        "static_prior_flags_high_risk": static_prior_flags_high_risk,
        "interaction_flags_new_risk": interaction_flags_new_risk,
        "static_prior_missed_high_risk": static_prior_missed_high_risk,
        "recovered_static_prior_miss": recovered_static_prior_miss,
        "interaction_false_alarm": interaction_false_alarm,
    }


def _source_key(ablation: dict[str, Any]) -> str:
    artifact_id = ablation["source_public_outcome_proxy_id"]
    for source_key in DEFAULT_SOURCE_KEYS:
        if source_key in artifact_id:
            return source_key
    if "anes-health" in artifact_id:
        return "anes_health_heldout"
    if "anes-climate" in artifact_id:
        return "anes_climate_heldout"
    return "htops_cost_pressure"


def _summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    case_count = len(case_results)
    flagged = [case for case in case_results if case["interaction_flags_new_risk"]]
    high_risk_flagged = [case for case in flagged if case["observed_high_risk"]]
    static_misses = [
        case for case in case_results if case["static_prior_missed_high_risk"]
    ]
    recovered = [
        case for case in static_misses if case["recovered_static_prior_miss"]
    ]
    false_alarms = [case for case in case_results if case["interaction_false_alarm"]]
    static_missed_high_risk_count = sum(
        1
        for case in case_results
        if case["observed_high_risk"] and not case["static_prior_flags_high_risk"]
    )
    interaction_missed_high_risk_count = sum(
        1
        for case in case_results
        if case["observed_high_risk"] and not case["interaction_flags_new_risk"]
    )
    return {
        "case_count": case_count,
        "interaction_flagged_case_count": len(flagged),
        "interaction_flagged_observed_high_risk_count": len(high_risk_flagged),
        "static_prior_miss_count": len(static_misses),
        "static_prior_miss_recovered_count": len(recovered),
        "false_alarm_count": len(false_alarms),
        "static_prior_miss_recovery_rate": _rate(len(recovered), len(static_misses)),
        "top_k_risk_hit_rate": _rate(len(high_risk_flagged), len(flagged)),
        "false_alarm_rate": _rate(len(false_alarms), len(flagged)),
        "decision_regret_reduction": (
            static_missed_high_risk_count - interaction_missed_high_risk_count
        ),
    }


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

    output_path = write_r6_decision_value_metrics(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "decision_value_passed": report["decision_value_passed"],
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
