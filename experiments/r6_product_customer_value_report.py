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
from experiments.r6_product_decision_report import build_r6_product_decision_report
from experiments.r6_research_product_value_support import (
    build_r6_research_product_value_support,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_PRODUCT_CUSTOMER_VALUE_REPORT_SCHEMA_VERSION = (
    "r6-product-customer-value-report-v1"
)
R6_PRODUCT_CUSTOMER_VALUE_SECTIONS = [
    "static_prior_baseline",
    "trend_direction",
    "risk_interval",
    "risk_distribution",
    "abnormal_segments",
    "mechanism_explanation",
    "research_support_gap_ledger",
    "evidence_and_blocked_claims",
    "outcome_review_plan",
]


def build_r6_product_customer_value_report(
    *,
    artifact_id: str,
    run_id: str,
    decision_report: dict[str, Any] | None = None,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    value_support: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    decision = decision_report or build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-current-001",
        run_id=run_id,
    )
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-current-001",
        run_id=run_id,
    )
    support = value_support or build_r6_research_product_value_support(
        artifact_id="r6-research-product-value-support-current-001",
        run_id=run_id,
        trend_interval_risk_metrics=metrics,
    )
    frontend_demo_ready = _frontend_demo_ready()
    source_registry = _source_registry(decision, metrics, support)
    report = {
        "schema_version": R6_PRODUCT_CUSTOMER_VALUE_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "customer_value_report_ready_guarded",
        "positioning": "人群反应趋势与风险区间模拟器",
        "customer_sections": R6_PRODUCT_CUSTOMER_VALUE_SECTIONS,
        "report_contract": {
            "source_backed_only": True,
            "static_narrative_fallback_allowed": False,
            "precise_point_prediction_allowed": False,
            "customer_facing_ui_demo_ready": frontend_demo_ready,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "display_payload": _display_payload(metrics, support),
        "section_contracts": _section_contracts(decision, metrics, support),
        "source_registry": source_registry,
        "source_refs": [entry["artifact_id"] for entry in source_registry],
        "blocked_claims": _unique_strings(
            [
                *decision.get("blocked_claims", []),
                *support.get("blocked_claims", []),
                "精准预测系统",
                "系统可以精确预测单点结果",
            ]
        ),
        "allowed_claims": [
            (
                "Product can display trend, interval, distribution, abnormal "
                "segments, and mechanism explanation from source-backed artifacts."
            ),
            (
                "Current output is guarded and does not claim field validation or "
                "precise point prediction."
            ),
        ],
        "blocking_gaps": _blocking_gaps(frontend_demo_ready),
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_product_customer_value_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_product_customer_value_report(**kwargs))


def _display_payload(
    metrics: dict[str, Any],
    support: dict[str, Any],
) -> dict[str, Any]:
    cases = metrics["case_results"]
    return {
        "trend_direction": {
            "summary_metric": metrics["summary"]["trend_direction_accuracy"],
            "support_status": _support_status(support, "trend_direction"),
            "cases": [
                {
                    "source_key": case["source_key"],
                    "trend_direction": case["trend_direction"],
                    "outcome_direction": case["outcome_direction"],
                    "matches_outcome": case["trend_direction_matches_outcome"],
                }
                for case in cases
            ],
        },
        "risk_interval": {
            "summary_metric": metrics["summary"]["interval_coverage"],
            "support_status": _support_status(support, "risk_interval"),
            "cases": [
                {
                    "source_key": case["source_key"],
                    "risk_interval": case["risk_interval"],
                    "observed_reject_proxy": case["observed_reject_proxy"],
                }
                for case in cases
            ],
        },
        "risk_distribution": {
            "risk_ranking_quality": metrics["summary"]["risk_ranking_quality"],
            "false_alarm_rate": metrics["summary"]["false_alarm_rate"],
            "support_status": _support_status(support, "risk_distribution"),
        },
        "abnormal_segments": [
            {
                "source_key": case["source_key"],
                "segments": case["top_abnormal_segments"],
                "support_status": _support_status(support, "abnormal_segments"),
            }
            for case in cases
        ],
        "mechanism_explanation": {
            "support_status": _support_status(support, "mechanism_explanation"),
            "claim_status": "diagnostic_only",
        },
        "research_support": {
            "overall_product_core_value_supported": support[
                "overall_product_core_value_supported"
            ],
            "support_coverage": support.get("support_coverage", {}),
            "product_claim_support_summary": support.get(
                "product_claim_support_summary",
                {},
            ),
            "research_next_task_execution_summary": support.get(
                "research_next_task_execution_summary",
                {},
            ),
            "support_gap_ledger": support.get("support_gap_ledger", []),
            "research_next_tasks": support.get("research_next_tasks", []),
        },
    }


def _section_contracts(
    decision: dict[str, Any],
    metrics: dict[str, Any],
    support: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "section_id": "static_prior_baseline",
            "source_artifact_ids": [decision["artifact_id"]],
        },
        {
            "section_id": "trend_direction",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "risk_interval",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "risk_distribution",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "abnormal_segments",
            "source_artifact_ids": [metrics["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "mechanism_explanation",
            "source_artifact_ids": [support["artifact_id"]],
        },
        {
            "section_id": "research_support_gap_ledger",
            "source_artifact_ids": [support["artifact_id"]],
        },
        {
            "section_id": "evidence_and_blocked_claims",
            "source_artifact_ids": [decision["artifact_id"], support["artifact_id"]],
        },
        {
            "section_id": "outcome_review_plan",
            "source_artifact_ids": [decision["artifact_id"]],
        },
    ]


def _source_registry(
    decision: dict[str, Any],
    metrics: dict[str, Any],
    support: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "artifact_id": decision["artifact_id"],
            "path": (
                "experiments/results/r6_product_decision_report/"
                "r6-product-decision-report-current-001.json"
            ),
        },
        {
            "artifact_id": metrics["artifact_id"],
            "path": (
                "experiments/results/r6_trend_interval_risk_metrics/"
                "r6-trend-interval-risk-metrics-current-001.json"
            ),
        },
        {
            "artifact_id": support["artifact_id"],
            "path": (
                "experiments/results/r6_research_product_value_support/"
                "r6-research-product-value-support-current-001.json"
            ),
        },
    ]


def _support_status(support: dict[str, Any], product_value: str) -> str:
    for item in support["support_matrix"]:
        if item["product_value"] == product_value:
            return item["support_status"]
    raise ValueError(f"missing support_matrix item: {product_value}")


def _unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _frontend_demo_ready() -> bool:
    repo_root = Path(__file__).resolve().parents[1]
    required_files = [
        repo_root / "demo" / "index.html",
        repo_root / "demo" / "app.js",
        repo_root / "demo" / "styles.css",
    ]
    return all(path.is_file() for path in required_files)


def _blocking_gaps(frontend_demo_ready: bool) -> list[str]:
    gaps = [
        "needs_field_outcome_validation",
        "needs_runtime_default_holdout_review",
    ]
    if frontend_demo_ready:
        gaps.append("needs_customer_workflow_runtime_integration")
    else:
        gaps.insert(0, "needs_customer_facing_ui_integration")
    return gaps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_product_customer_value_report(
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
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
