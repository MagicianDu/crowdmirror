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
from experiments.r6_mechanism_research_readiness_report import (
    build_r6_mechanism_research_readiness_report,
)
from experiments.r6_trend_interval_risk_metrics import (
    R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION,
    build_r6_trend_interval_risk_metrics,
)


R6_RESEARCH_PRODUCT_VALUE_SUPPORT_SCHEMA_VERSION = (
    "r6-research-product-value-support-v1"
)
SUPPORTED_TREND_METRIC_STATUSES = {
    "trend_interval_risk_supported",
    "trend_interval_risk_partial_high_false_alarm",
}


def build_r6_research_product_value_support(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    mechanism_readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-current-001",
        run_id=run_id,
    )
    mechanism = mechanism_readiness or build_r6_mechanism_research_readiness_report(
        artifact_id="r6-mechanism-research-readiness-report-current-001",
        run_id=run_id,
    )
    _validate_metrics(metrics)
    summary = metrics["summary"]
    support_matrix = [
        {
            "product_value": "trend_direction",
            "support_status": _threshold_support(
                summary["trend_direction_accuracy"],
                pass_threshold=0.80,
            ),
            "source_metric": "trend_direction_accuracy",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "risk_interval",
            "support_status": _threshold_support(
                summary["interval_coverage"],
                pass_threshold=0.80,
            ),
            "source_metric": "interval_coverage",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "risk_distribution",
            "support_status": (
                "partial_high_false_alarm"
                if summary["false_alarm_rate"] > 0.50
                else "supported_current_proxy"
            ),
            "source_metric": "risk_ranking_quality",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "abnormal_segments",
            "support_status": "diagnostic_only",
            "source_metric": "abnormal_segment_recall",
            "source_artifact_ids": [metrics["artifact_id"]],
        },
        {
            "product_value": "mechanism_explanation",
            "support_status": "diagnostic_only",
            "source_metric": "mechanism_research_status",
            "source_artifact_ids": [mechanism["artifact_id"]],
        },
        {
            "product_value": "outcome_feedback_learning",
            "support_status": "blocked_until_holdout_or_field_outcome",
            "source_metric": "runtime_default_allowed",
            "source_artifact_ids": [mechanism["artifact_id"]],
        },
    ]
    overall_supported = all(
        item["support_status"].startswith("supported")
        for item in support_matrix
    )
    report = {
        "schema_version": R6_RESEARCH_PRODUCT_VALUE_SUPPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "product_value_support_ready"
            if overall_supported
            else "product_value_support_partial"
        ),
        "overall_product_core_value_supported": overall_supported,
        "support_matrix": support_matrix,
        "source_refs": [metrics["artifact_id"], mechanism["artifact_id"]],
        "allowed_claims": [
            (
                "Research evidence can support guarded trend and interval reporting "
                "as partial current-proxy evidence."
            ),
            (
                "Risk distribution, abnormal segments, mechanism explanation, and "
                "outcome feedback remain guarded until false-alarm and holdout gaps "
                "close."
            ),
        ],
        "blocked_claims": [
            "精准预测系统",
            "系统可以精确预测单点结果",
            "field validation 已完成",
            "runtime default 可以开启",
            "Research 已完整支撑 Product 全部核心价值",
        ],
        "blocking_gaps": []
        if overall_supported
        else [
            "needs_trend_interval_holdout_support",
            "needs_false_alarm_control",
            "needs_field_outcome_validation",
            "needs_runtime_default_holdout_review",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_research_product_value_support(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r6_research_product_value_support(**kwargs))


def _validate_metrics(metrics: dict[str, Any]) -> None:
    if metrics.get("schema_version") != R6_TREND_INTERVAL_RISK_METRICS_SCHEMA_VERSION:
        raise ValueError("trend_interval_risk_metrics.schema_version is invalid")
    status = metrics.get("status")
    if status not in SUPPORTED_TREND_METRIC_STATUSES:
        raise ValueError("trend_interval_risk_metrics.status is invalid")
    if not isinstance(metrics.get("summary"), dict):
        raise ValueError("trend_interval_risk_metrics.summary must be an object")
    non_empty_string(
        metrics.get("artifact_id"),
        field="trend_interval_risk_metrics.artifact_id",
    )


def _threshold_support(value: float, *, pass_threshold: float) -> str:
    if value >= pass_threshold:
        return "supported_current_proxy"
    if value > 0:
        return "partial_current_proxy"
    return "blocked"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_research_product_value_support(
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
                "overall_product_core_value_supported": report[
                    "overall_product_core_value_supported"
                ],
                "status": report["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
