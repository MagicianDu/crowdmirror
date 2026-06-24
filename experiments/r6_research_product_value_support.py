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
from experiments.r6_research_next_task_execution import (
    build_r6_research_next_task_execution,
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
    next_task_execution: dict[str, Any] | None = None,
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
    task_execution = next_task_execution or build_r6_research_next_task_execution(
        artifact_id="r6-research-next-task-execution-current-001",
        run_id=run_id,
        trend_interval_risk_metrics=metrics,
    )
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
    support_gap_ledger = _support_gap_ledger(
        support_matrix=support_matrix,
        summary=summary,
        mechanism=mechanism,
    )
    research_next_tasks = _research_next_tasks(support_gap_ledger)
    support_coverage = _support_coverage(support_matrix)
    product_claim_support_summary = _product_claim_support_summary(
        support_gap_ledger=support_gap_ledger,
        overall_supported=overall_supported,
    )
    task_execution_summary = _task_execution_summary(task_execution)
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
        "support_coverage": support_coverage,
        "support_gap_ledger": support_gap_ledger,
        "research_next_tasks": research_next_tasks,
        "research_next_task_execution_summary": task_execution_summary,
        "product_claim_support_summary": product_claim_support_summary,
        "acceptance_gates": {
            "all_product_values_mapped": len(support_gap_ledger) == 6,
            "all_gaps_have_research_tasks": all(
                bool(item["next_research_task_id"]) for item in support_gap_ledger
            ),
            "all_tasks_have_acceptance_criteria": all(
                bool(task["acceptance_criteria"]) for task in research_next_tasks
            ),
            "research_next_tasks_executed": task_execution["acceptance_gates"][
                "all_five_tasks_executed"
            ],
            "research_support_contract_complete": (
                len(support_gap_ledger) == 6
                and all(
                    bool(item["next_research_task_id"])
                    for item in support_gap_ledger
                )
                and all(
                    bool(task["acceptance_criteria"])
                    for task in research_next_tasks
                )
                and task_execution["acceptance_gates"]["all_five_tasks_executed"]
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "overall_product_core_value_supported": overall_supported,
        },
        "source_refs": [
            metrics["artifact_id"],
            mechanism["artifact_id"],
            task_execution["artifact_id"],
        ],
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


def _task_execution_summary(task_execution: dict[str, Any]) -> dict[str, Any]:
    summary = task_execution["execution_summary"]
    return {
        "artifact_id": task_execution["artifact_id"],
        "status": task_execution["status"],
        "task_count": summary["task_count"],
        "accepted_for_guarded_reporting_count": summary[
            "accepted_for_guarded_reporting_count"
        ],
        "blocked_or_failed_count": summary["blocked_or_failed_count"],
        "product_core_value_fully_supported": summary[
            "product_core_value_fully_supported"
        ],
    }


def _support_gap_ledger(
    *,
    support_matrix: list[dict[str, Any]],
    summary: dict[str, Any],
    mechanism: dict[str, Any],
) -> list[dict[str, Any]]:
    by_value = {item["product_value"]: item for item in support_matrix}
    mechanism_summary = mechanism.get("readiness_summary", {})
    return [
        _ledger_entry(
            by_value["trend_direction"],
            current_metric_value=summary["trend_direction_accuracy"],
            target_threshold=0.80,
            gap_to_target=_positive_gap(0.80, summary["trend_direction_accuracy"]),
            product_display_level="guarded_partial_claim",
            blocking_gap_ids=[
                "needs_trend_interval_holdout_support",
                "needs_independent_or_field_outcome_support",
            ],
            next_research_task_id="r6-research-task-trend-interval-holdout",
            acceptance_criteria=(
                "independent_or_field_holdout.trend_direction_accuracy >= 0.80 "
                "with no hidden false-alarm regression"
            ),
        ),
        _ledger_entry(
            by_value["risk_interval"],
            current_metric_value=summary["interval_coverage"],
            target_threshold=0.80,
            gap_to_target=_positive_gap(0.80, summary["interval_coverage"]),
            product_display_level="guarded_partial_claim",
            blocking_gap_ids=[
                "needs_trend_interval_holdout_support",
                "needs_interval_calibration_holdout",
            ],
            next_research_task_id="r6-research-task-trend-interval-holdout",
            acceptance_criteria=(
                "independent_or_field_holdout.interval_coverage >= 0.80 and "
                "mean_interval_width remains decision-usable"
            ),
        ),
        _ledger_entry(
            by_value["risk_distribution"],
            current_metric_value={
                "risk_ranking_quality": summary["risk_ranking_quality"],
                "false_alarm_rate": summary["false_alarm_rate"],
            },
            target_threshold={
                "risk_ranking_quality_min": 0.50,
                "false_alarm_rate_max": 0.50,
            },
            gap_to_target={
                "risk_ranking_gap": _positive_gap(
                    0.50,
                    summary["risk_ranking_quality"],
                ),
                "false_alarm_gap": _positive_gap(
                    summary["false_alarm_rate"],
                    0.50,
                ),
            },
            product_display_level="guarded_diagnostic_claim",
            blocking_gap_ids=[
                "needs_false_alarm_control",
                "needs_risk_ranking_holdout_support",
            ],
            next_research_task_id="r6-research-task-false-alarm-control",
            acceptance_criteria=(
                "risk_ranking_quality >= 0.50 and false_alarm_rate <= 0.50 "
                "on independent_or_field_holdout"
            ),
        ),
        _ledger_entry(
            by_value["abnormal_segments"],
            current_metric_value=summary["abnormal_segment_recall"],
            target_threshold={
                "abnormal_segment_recall_min": 0.80,
                "observed_segment_labels_required": True,
            },
            gap_to_target={"observed_segment_labels_missing": True},
            product_display_level="diagnostic_claim_only",
            blocking_gap_ids=[
                "needs_segment_level_outcome_labels",
                "needs_abnormal_segment_precision_recall",
            ],
            next_research_task_id="r6-research-task-segment-outcome-labels",
            acceptance_criteria=(
                "segment-level outcome or expert audit labels exist and "
                "abnormal_segment_precision_recall is reportable"
            ),
        ),
        _ledger_entry(
            by_value["mechanism_explanation"],
            current_metric_value=mechanism.get("status"),
            target_threshold={
                "mechanism_holdout_validation_required": True,
                "operator_holdout_non_regression_required": True,
            },
            gap_to_target={
                "mechanism_regression_case_count": mechanism_summary.get(
                    "mechanism_regression_case_count"
                ),
                "operator_holdout_passed_trial_count": mechanism_summary.get(
                    "operator_holdout_passed_trial_count"
                ),
            },
            product_display_level="diagnostic_claim_only",
            blocking_gap_ids=[
                "needs_mechanism_holdout_validation",
                "needs_operator_holdout_validation",
            ],
            next_research_task_id="r6-research-task-mechanism-holdout-validation",
            acceptance_criteria=(
                "mechanism ablation no longer regresses on holdout and "
                "operator_holdout_non_regression is true"
            ),
        ),
        _ledger_entry(
            by_value["outcome_feedback_learning"],
            current_metric_value={
                "runtime_default_allowed": mechanism.get("decision", {}).get(
                    "runtime_default_allowed"
                ),
                "operator_holdout_passed_trial_count": mechanism_summary.get(
                    "operator_holdout_passed_trial_count"
                ),
            },
            target_threshold={
                "runtime_default_allowed": True,
                "requires_field_or_independent_holdout": True,
            },
            gap_to_target={
                "runtime_default_blocked": True,
                "field_outcome_validated": False,
            },
            product_display_level="blocked_claim_only",
            blocking_gap_ids=[
                "needs_runtime_default_holdout_review",
                "needs_field_outcome_validation",
                "needs_cross_case_operator_transfer",
            ],
            next_research_task_id="r6-research-task-outcome-feedback-transfer",
            acceptance_criteria=(
                "candidate update passes cross-case transfer, independent holdout, "
                "and field outcome review before runtime default"
            ),
        ),
    ]


def _ledger_entry(
    matrix_item: dict[str, Any],
    *,
    current_metric_value: Any,
    target_threshold: Any,
    gap_to_target: Any,
    product_display_level: str,
    blocking_gap_ids: list[str],
    next_research_task_id: str,
    acceptance_criteria: str,
) -> dict[str, Any]:
    return {
        "product_value": matrix_item["product_value"],
        "current_support_status": matrix_item["support_status"],
        "product_display_level": product_display_level,
        "source_metric": matrix_item["source_metric"],
        "current_metric_value": current_metric_value,
        "target_threshold": target_threshold,
        "gap_to_target": gap_to_target,
        "blocking_gap_ids": blocking_gap_ids,
        "next_research_task_id": next_research_task_id,
        "acceptance_criteria": acceptance_criteria,
        "source_artifact_ids": matrix_item["source_artifact_ids"],
    }


def _research_next_tasks(
    support_gap_ledger: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    definitions = {
        "r6-research-task-trend-interval-holdout": {
            "goal": "验证趋势方向和风险区间在独立 holdout 或真实 outcome 上是否稳定。",
            "implementation_path": (
                "接入同 family / field outcome holdout，复用 trend_interval_risk_metrics，"
                "报告 direction accuracy、interval coverage、interval width 和 false alarm。"
            ),
            "acceptance_criteria": (
                "trend_direction_accuracy >= 0.80 且 interval_coverage >= 0.80，"
                "同时不隐藏 false alarm。"
            ),
        },
        "r6-research-task-false-alarm-control": {
            "goal": "降低风险排序误报，让 Product 的风险分布从诊断走向可决策。",
            "implementation_path": (
                "设计非 case-memory 的 false-alarm discriminator，绑定 holdout 验证，"
                "同时报告 risk_ranking_quality 和 false_alarm_rate。"
            ),
            "acceptance_criteria": (
                "risk_ranking_quality >= 0.50 且 false_alarm_rate <= 0.50，"
                "并通过独立或 field holdout。"
            ),
        },
        "r6-research-task-segment-outcome-labels": {
            "goal": "把异常群体从可解释展示升级为可验证指标。",
            "implementation_path": (
                "为 segment-level outcome 或专家审核建立轻量标签协议，"
                "输出 abnormal segment precision/recall。"
            ),
            "acceptance_criteria": (
                "存在可审计 segment labels，且 abnormal segment precision/recall 可计算。"
            ),
        },
        "r6-research-task-mechanism-holdout-validation": {
            "goal": "验证机制解释和 behavioral operator 不只是诊断路径。",
            "implementation_path": (
                "对 mechanism propagation、mechanism ablation 和 operator holdout "
                "做同 family / independent holdout 复核。"
            ),
            "acceptance_criteria": (
                "mechanism ablation 不再出现 holdout regression，"
                "operator_holdout_non_regression=true。"
            ),
        },
        "r6-research-task-outcome-feedback-transfer": {
            "goal": "证明 outcome feedback learning 能受控迁移，而不是 same-case 修补。",
            "implementation_path": (
                "用真实 outcome 或独立 holdout 审核 candidate update，"
                "通过 cross-case transfer 和 runtime update guard 后才允许默认启用。"
            ),
            "acceptance_criteria": (
                "candidate update 通过 cross-case transfer、independent holdout "
                "和 field outcome review；runtime_default_allowed 才能为 true。"
            ),
        },
    }
    task_ids = list(
        dict.fromkeys(item["next_research_task_id"] for item in support_gap_ledger)
    )
    tasks = []
    for task_id in task_ids:
        task = definitions[task_id]
        tasks.append(
            {
                "task_id": task_id,
                "goal": task["goal"],
                "implementation_path": task["implementation_path"],
                "acceptance_criteria": task["acceptance_criteria"],
                "unblocks_product_values": [
                    item["product_value"]
                    for item in support_gap_ledger
                    if item["next_research_task_id"] == task_id
                ],
            }
        )
    return tasks


def _support_coverage(support_matrix: list[dict[str, Any]]) -> dict[str, Any]:
    categories = [_support_category(item["support_status"]) for item in support_matrix]
    return {
        "product_value_count": len(support_matrix),
        "supported_value_count": categories.count("supported"),
        "partial_value_count": categories.count("partial"),
        "diagnostic_value_count": categories.count("diagnostic"),
        "blocked_value_count": categories.count("blocked"),
        "research_support_contract_complete": True,
    }


def _product_claim_support_summary(
    *,
    support_gap_ledger: list[dict[str, Any]],
    overall_supported: bool,
) -> dict[str, Any]:
    return {
        "research_support_contract_complete": True,
        "overall_product_core_value_supported": overall_supported,
        "guarded_partial_claims_supported": [
            item["product_value"]
            for item in support_gap_ledger
            if item["product_display_level"] == "guarded_partial_claim"
        ],
        "diagnostic_only_claims": [
            item["product_value"]
            for item in support_gap_ledger
            if item["product_display_level"]
            in {"guarded_diagnostic_claim", "diagnostic_claim_only"}
        ],
        "blocked_product_values": [
            item["product_value"]
            for item in support_gap_ledger
            if item["product_display_level"] == "blocked_claim_only"
        ],
    }


def _support_category(status: str) -> str:
    if status.startswith("supported"):
        return "supported"
    if status == "partial_current_proxy":
        return "partial"
    if status in {"partial_high_false_alarm", "diagnostic_only"}:
        return "diagnostic"
    return "blocked"


def _positive_gap(target: float, current: float) -> float:
    return round(max(0.0, target - current), 3)


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
