from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_ablation_report import build_r6_ablation_report
from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)
from experiments.r6_decision_value_metrics import (
    DEFAULT_SOURCE_KEYS,
    build_r6_decision_value_metrics,
)
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION = (
    "r6-trend-interval-risk-metrics-v1"
)


def build_r6_trend_interval_risk_metrics(
    *,
    artifact_id: str,
    run_id: str,
    source_keys: list[str] | None = None,
    ablation_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    reports = ablation_reports or _build_default_ablation_reports(
        artifact_id=artifact_id,
        run_id=run_id,
        source_keys=source_keys or DEFAULT_SOURCE_KEYS,
    )
    decision_value = build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value",
        run_id=run_id,
        ablation_reports=reports,
    )
    case_results = [
        _case_metrics(report, decision_case)
        for report, decision_case in zip(reports, decision_value["case_results"])
    ]
    summary = _summary(case_results, decision_value["summary"])
    supports_product = (
        summary["trend_direction_accuracy"] >= 0.80
        and summary["interval_coverage"] >= 0.80
        and summary["risk_ranking_quality"] >= 0.50
        and summary["false_alarm_rate"] <= 0.50
    )
    status = (
        "trend_interval_risk_supported"
        if supports_product
        else "trend_interval_risk_partial_high_false_alarm"
    )
    report = {
        "schema_version": R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "research_supports_product_core_value": supports_product,
        "metric_definition": {
            "trend_direction_accuracy": (
                "Share of cases where interaction direction matches observed/proxy "
                "direction relative to static prior."
            ),
            "interval_coverage": (
                "Share of cases where observed/proxy reject rate falls inside the "
                "interaction risk interval."
            ),
            "risk_ranking_quality": (
                "Share of interaction-flagged high-risk cases that are observed/proxy "
                "high risk."
            ),
            "abnormal_segment_recall": (
                "Share of cases with at least one positive-delta segment surfaced as "
                "an abnormal segment."
            ),
            "false_alarm_rate": (
                "Share of interaction-flagged cases that are not observed/proxy high "
                "risk."
            ),
        },
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": {
            "trend_direction_metric_present": True,
            "interval_coverage_metric_present": True,
            "risk_ranking_metric_present": True,
            "abnormal_segment_metric_present": True,
            "trend_direction_passed": summary["trend_direction_accuracy"] >= 0.80,
            "interval_coverage_passed": summary["interval_coverage"] >= 0.80,
            "risk_ranking_passed": summary["risk_ranking_quality"] >= 0.50,
            "false_alarm_control_passed": summary["false_alarm_rate"] <= 0.50,
            "research_supports_product_core_value": supports_product,
        },
        "source_refs": [case["source_ablation_artifact_id"] for case in case_results],
        "allowed_claims": [
            (
                "Research can report trend direction, risk interval, risk ranking, "
                "abnormal segments, and false-alarm status as auditable metrics."
            ),
        ],
        "blocked_claims": [
            "精准预测系统",
            "系统可以精确预测单点结果",
            "field validation 已完成",
            "runtime default 可以开启",
            "accuracy superiority established",
        ],
        "blocking_gaps": []
        if supports_product
        else [
            "needs_lower_false_alarm_rate",
            "needs_independent_or_field_outcome_support",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_trend_interval_risk_metrics(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_trend_interval_risk_metrics(**kwargs))


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


def _case_metrics(
    ablation: dict[str, Any],
    decision_case: dict[str, Any],
) -> dict[str, Any]:
    static = float(decision_case["static_prior_prediction"])
    interaction = float(decision_case["interaction_prediction"])
    observed = float(decision_case["observed_reject_proxy"])
    delta = round(interaction - static, 3)
    trend_direction = _direction(delta)
    outcome_direction = _direction(round(observed - static, 3))
    interval_half_width = max(0.05, abs(delta) + 0.05)
    lower = round(max(0.0, interaction - interval_half_width), 3)
    upper = round(min(1.0, interaction + interval_half_width), 3)
    top_segments = _top_abnormal_segments(ablation)
    return {
        "source_ablation_artifact_id": ablation["artifact_id"],
        "source_key": decision_case["source_key"],
        "target_case_id": decision_case["target_case_id"],
        "static_prior_prediction": round(static, 3),
        "interaction_prediction": round(interaction, 3),
        "observed_reject_proxy": round(observed, 3),
        "trend_direction": trend_direction,
        "outcome_direction": outcome_direction,
        "trend_direction_matches_outcome": trend_direction == outcome_direction,
        "risk_interval": {
            "lower": lower,
            "upper": upper,
            "width": round(upper - lower, 3),
            "contains_observed": lower <= observed <= upper,
        },
        "risk_ranking_hit": (
            bool(decision_case["interaction_flags_new_risk"])
            and bool(decision_case["observed_high_risk"])
        ),
        "interaction_false_alarm": bool(decision_case["interaction_false_alarm"]),
        "top_abnormal_segments": top_segments,
        "abnormal_segment_detected": bool(top_segments),
    }


def _direction(delta: float) -> str:
    if delta > 0:
        return "risk_up"
    if delta < 0:
        return "risk_down"
    return "flat"


def _top_abnormal_segments(ablation: dict[str, Any]) -> list[dict[str, Any]]:
    template = get_r6_case_template(ablation["target_case_id"])
    segments = template["interaction_profile"]["segment_shifts"]
    normalized = [
        {
            "segment_id": segment["segment_id"],
            "delta_reject": round(float(segment["delta_distribution"]["reject"]), 3),
            "mechanisms": list(segment.get("mechanisms", [])),
        }
        for segment in segments
        if float(segment["delta_distribution"]["reject"]) > 0
    ]
    return sorted(
        normalized,
        key=lambda item: item["delta_reject"],
        reverse=True,
    )[:3]


def _summary(
    case_results: list[dict[str, Any]],
    decision_summary: dict[str, Any],
) -> dict[str, Any]:
    case_count = len(case_results)
    trend_matches = sum(
        1 for case in case_results if case["trend_direction_matches_outcome"]
    )
    interval_hits = sum(
        1 for case in case_results if case["risk_interval"]["contains_observed"]
    )
    abnormal_hits = sum(
        1 for case in case_results if case["abnormal_segment_detected"]
    )
    return {
        "case_count": case_count,
        "trend_direction_accuracy": _rate(trend_matches, case_count),
        "interval_coverage": _rate(interval_hits, case_count),
        "mean_interval_width": round(
            sum(case["risk_interval"]["width"] for case in case_results) / case_count,
            3,
        ),
        "risk_ranking_quality": decision_summary["top_k_risk_hit_rate"],
        "abnormal_segment_recall": _rate(abnormal_hits, case_count),
        "false_alarm_rate": decision_summary["false_alarm_rate"],
        "decision_regret_reduction": decision_summary["decision_regret_reduction"],
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

    output_path = write_r6_trend_interval_risk_metrics(
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
                "research_supports_product_core_value": report[
                    "research_supports_product_core_value"
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
