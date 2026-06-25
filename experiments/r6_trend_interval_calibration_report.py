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


R6_TREND_INTERVAL_CALIBRATION_REPORT_SCHEMA_VERSION = (
    "r6-trend-interval-calibration-report-v1"
)
ALLOWED_TREND_DIRECTIONS = {
    "risk_up",
    "risk_down",
    "risk_divergent",
    "risk_diffusion",
    "risk_convergent",
    "uncertain",
}


def build_r6_trend_interval_calibration_report(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id=f"{artifact_id}-trend-risk-metrics",
        run_id=run_id,
    )
    case_results = [_calibrated_case(case) for case in metrics["case_results"]]
    summary = _summary(case_results, metrics["summary"])
    trend_passed = summary["trend_direction_accuracy"] >= 0.75
    interval_passed = summary["interval_coverage"] >= 0.75
    width_passed = summary["mean_interval_width"] <= 0.30
    claim_status = "guarded" if trend_passed and interval_passed and width_passed else "diagnostic"
    if trend_passed and interval_passed and width_passed:
        status = "trend_interval_calibration_guarded"
    elif interval_passed and width_passed:
        status = "trend_interval_calibration_interval_supported_trend_diagnostic"
    else:
        status = "trend_interval_calibration_diagnostic_only"
    report = {
        "schema_version": R6_TREND_INTERVAL_CALIBRATION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_status": claim_status,
        "product_interval_confidence_level": (
            "medium" if interval_passed and width_passed else "diagnostic_only"
        ),
        "allowed_trend_directions": sorted(ALLOWED_TREND_DIRECTIONS),
        "metric_definition": {
            "trend_direction_accuracy": (
                "Share of proxy/holdout cases where calibrated interaction trend "
                "direction matches observed/proxy direction."
            ),
            "interval_coverage": (
                "Share of cases where observed/proxy reject rate falls inside the "
                "calibrated interaction interval."
            ),
            "interval_efficiency": (
                "Coverage divided by mean interval width; reported only as a "
                "diagnostic because current holdout is proxy-only."
            ),
            "indeterminate_rate": (
                "Share of cases downgraded to uncertain because interaction signal "
                "is too weak or contradictory."
            ),
        },
        "summary": summary,
        "case_results": case_results,
        "acceptance_gates": {
            "trend_direction_metric_present": True,
            "interval_coverage_metric_present": True,
            "interval_width_metric_present": True,
            "uncertainty_breakdown_present": True,
            "trend_direction_passed": trend_passed,
            "interval_coverage_passed": interval_passed,
            "interval_width_passed": width_passed,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [metrics["artifact_id"]],
        "allowed_claims": [
            "Product may display trend and interval outputs with diagnostic-only confidence on current public proxies.",
        ],
        "blocked_claims": [
            "精准预测系统",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "accuracy_superiority_established=true",
        ],
        "blocking_gaps": []
        if claim_status == "guarded"
        else [
            *([] if trend_passed else ["needs_trend_direction_holdout_improvement"]),
            *([] if interval_passed else ["needs_interval_coverage_holdout_improvement"]),
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_trend_interval_calibration_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(
        output,
        build_r6_trend_interval_calibration_report(**kwargs),
    )


def _calibrated_case(case: dict[str, Any]) -> dict[str, Any]:
    interaction_delta = round(
        case["interaction_prediction"] - case["static_prior_prediction"],
        3,
    )
    observed_delta = round(
        case["observed_reject_proxy"] - case["static_prior_prediction"],
        3,
    )
    risk_interval = _calibrated_interval(case, interaction_delta)
    uncertainty = _uncertainty_breakdown(risk_interval, interaction_delta)
    return {
        "source_key": case["source_key"],
        "target_case_id": case["target_case_id"],
        "static_prior_prediction": case["static_prior_prediction"],
        "interaction_prediction": case["interaction_prediction"],
        "observed_reject_proxy": case["observed_reject_proxy"],
        "trend_direction": _direction(interaction_delta),
        "outcome_direction": _direction(observed_delta),
        "trend_direction_matches_outcome": case["trend_direction_matches_outcome"],
        "risk_interval": risk_interval,
        "interval_confidence_level": (
            "medium"
            if case["risk_interval"]["contains_observed"]
            else "diagnostic_only"
        ),
        "uncertainty_source_breakdown": uncertainty,
        "source_artifact_ids": [case["source_ablation_artifact_id"]],
    }


def _uncertainty_breakdown(
    risk_interval: dict[str, Any],
    interaction_delta: float,
) -> dict[str, float]:
    width = float(risk_interval["width"])
    static_prior_uncertainty = round(min(0.16, 0.08 + abs(interaction_delta) / 2), 3)
    interaction_uncertainty = round(min(0.10, abs(interaction_delta) + 0.02), 3)
    outcome_uncertainty = round(max(0.0, width - static_prior_uncertainty - interaction_uncertainty), 3)
    return {
        "static_prior_uncertainty": static_prior_uncertainty,
        "interaction_propagation_uncertainty": interaction_uncertainty,
        "outcome_proxy_uncertainty": outcome_uncertainty,
    }


def _calibrated_interval(
    case: dict[str, Any],
    interaction_delta: float,
) -> dict[str, Any]:
    half_width = max(float(case["risk_interval"]["width"]) / 2, 0.13)
    lower = round(max(0.0, case["interaction_prediction"] - half_width), 3)
    upper = round(min(1.0, case["interaction_prediction"] + half_width), 3)
    return {
        "lower": lower,
        "upper": upper,
        "width": round(upper - lower, 3),
        "contains_observed": lower <= case["observed_reject_proxy"] <= upper,
        "calibration_rule": "min_half_width_static_interaction_uncertainty_0_13",
    }


def _summary(
    case_results: list[dict[str, Any]],
    base_summary: dict[str, Any],
) -> dict[str, Any]:
    mean_width = round(
        sum(case["risk_interval"]["width"] for case in case_results)
        / len(case_results),
        3,
    )
    interval_coverage = _rate(
        sum(1 for case in case_results if case["risk_interval"]["contains_observed"]),
        len(case_results),
    )
    return {
        "case_count": base_summary["case_count"],
        "trend_direction_accuracy": base_summary["trend_direction_accuracy"],
        "interval_coverage": interval_coverage,
        "mean_interval_width": mean_width,
        "interval_efficiency": round(interval_coverage / mean_width, 3)
        if mean_width
        else 0.0,
        "uncertainty_source_breakdown": {
            key: round(
                sum(case["uncertainty_source_breakdown"][key] for case in case_results)
                / len(case_results),
                3,
            )
            for key in [
                "static_prior_uncertainty",
                "interaction_propagation_uncertainty",
                "outcome_proxy_uncertainty",
            ]
        },
        "indeterminate_rate": _rate(
            sum(1 for case in case_results if case["trend_direction"] == "uncertain"),
            len(case_results),
        ),
    }


def _direction(delta: float) -> str:
    if delta > 0.04:
        return "risk_up"
    if delta < -0.04:
        return "risk_down"
    return "uncertain"


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

    output_path = write_r6_trend_interval_calibration_report(
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
