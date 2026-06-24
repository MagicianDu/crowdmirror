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
from experiments.r6_cross_case_transfer_protocol import (
    build_r6_cross_case_transfer_protocol,
)
from experiments.r6_decision_value_metrics import build_r6_decision_value_metrics
from experiments.r6_interaction_signal_validity import (
    build_r6_interaction_signal_validity,
)
from experiments.r6_operator_holdout_validation import (
    build_r6_operator_holdout_validation,
)
from experiments.r6_trend_interval_risk_metrics import (
    build_r6_trend_interval_risk_metrics,
)


R6_RESEARCH_NEXT_TASK_EXECUTION_SCHEMA_VERSION = (
    "r6-research-next-task-execution-v1"
)


def build_r6_research_next_task_execution(
    *,
    artifact_id: str,
    run_id: str,
    trend_interval_risk_metrics: dict[str, Any] | None = None,
    decision_value_metrics: dict[str, Any] | None = None,
    interaction_signal_validity: dict[str, Any] | None = None,
    operator_holdout_validation: dict[str, Any] | None = None,
    cross_case_transfer_protocol: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    metrics = trend_interval_risk_metrics or build_r6_trend_interval_risk_metrics(
        artifact_id="r6-trend-interval-risk-metrics-current-001",
        run_id=run_id,
    )
    decision = decision_value_metrics or build_r6_decision_value_metrics(
        artifact_id=f"{artifact_id}-decision-value-metrics",
        run_id=run_id,
    )
    signal_validity = (
        interaction_signal_validity
        or build_r6_interaction_signal_validity(
            artifact_id=f"{artifact_id}-interaction-signal-validity",
            run_id=run_id,
            decision_value_metrics=decision,
        )
    )
    operator_holdout = (
        operator_holdout_validation
        or build_r6_operator_holdout_validation(
            artifact_id="r6-operator-holdout-validation-current-001",
            run_id=run_id,
        )
    )
    transfer_protocol = (
        cross_case_transfer_protocol
        or build_r6_cross_case_transfer_protocol(
            artifact_id="r6-cross-case-transfer-protocol-current-002",
            run_id=run_id,
        )
    )
    task_results = [
        _trend_interval_holdout_task(metrics),
        _false_alarm_control_task(
            decision_value_metrics=decision,
            signal_validity=signal_validity,
        ),
        _segment_outcome_labels_task(metrics),
        _mechanism_holdout_validation_task(operator_holdout),
        _outcome_feedback_transfer_task(transfer_protocol),
    ]
    report = {
        "schema_version": R6_RESEARCH_NEXT_TASK_EXECUTION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "research_next_tasks_executed_with_guarded_results",
        "task_results": task_results,
        "execution_summary": _execution_summary(task_results),
        "acceptance_gates": {
            "all_five_tasks_executed": len(task_results) == 5
            and all(task["execution_status"] == "executed" for task in task_results),
            "all_task_results_have_source_refs": all(
                bool(task["source_artifact_ids"]) for task in task_results
            ),
            "all_task_results_have_acceptance_decision": all(
                bool(task["acceptance_decision"]) for task in task_results
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "product_core_value_fully_supported": False,
        },
        "source_refs": _unique_strings(
            source_ref
            for task in task_results
            for source_ref in task["source_artifact_ids"]
        ),
        "allowed_claims": [
            "All five Research next tasks have executable, source-backed task results.",
            "Some tasks provide guarded or diagnostic evidence; blocked gates remain visible.",
        ],
        "blocked_claims": [
            "Research 已完整支撑 Product 全部核心价值",
            "field validation 已完成",
            "runtime default 可以开启",
            "精准预测系统",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r6_research_next_task_execution(
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r6_research_next_task_execution(**kwargs))


def _trend_interval_holdout_task(metrics: dict[str, Any]) -> dict[str, Any]:
    summary = metrics["summary"]
    trend_passed = summary["trend_direction_accuracy"] >= 0.80
    interval_passed = summary["interval_coverage"] >= 0.80
    false_alarm_passed = summary["false_alarm_rate"] <= 0.50
    return _task_result(
        task_id="r6-research-task-trend-interval-holdout",
        product_values=["trend_direction", "risk_interval"],
        acceptance_decision=(
            "accepted_for_guarded_reporting"
            if trend_passed and interval_passed and false_alarm_passed
            else "failed_current_public_proxy_gate"
        ),
        metrics={
            "trend_direction_accuracy": summary["trend_direction_accuracy"],
            "interval_coverage": summary["interval_coverage"],
            "mean_interval_width": summary["mean_interval_width"],
            "false_alarm_rate": summary["false_alarm_rate"],
        },
        acceptance_gates={
            "current_public_proxy_holdout_executed": True,
            "trend_direction_accuracy_passed": trend_passed,
            "interval_coverage_passed": interval_passed,
            "false_alarm_not_hidden": false_alarm_passed,
            "field_outcome_validated": False,
        },
        source_artifact_ids=[metrics["artifact_id"]],
    )


def _false_alarm_control_task(
    *,
    decision_value_metrics: dict[str, Any],
    signal_validity: dict[str, Any],
) -> dict[str, Any]:
    case_by_source = {
        case["source_key"]: case for case in decision_value_metrics["case_results"]
    }
    selected_source_keys = [
        score["audit"]["source_key"]
        for score in signal_validity["case_validity_scores"]
        if score["classification"] == "diagnostic_only"
    ]
    selected_cases = [case_by_source[source_key] for source_key in selected_source_keys]
    true_positive_count = sum(
        1 for case in decision_value_metrics["case_results"] if case["recovered_static_prior_miss"]
    )
    true_positive_kept = sum(
        1 for case in selected_cases if case["recovered_static_prior_miss"]
    )
    false_alarm_kept = sum(1 for case in selected_cases if case["interaction_false_alarm"])
    predicted_risk_count = len(selected_cases)
    controlled_false_alarm_rate = _rate(false_alarm_kept, predicted_risk_count)
    controlled_ranking_quality = _rate(true_positive_kept, predicted_risk_count)
    controlled_recovery_rate = _rate(true_positive_kept, true_positive_count)
    current_proxy_control_passed = (
        controlled_false_alarm_rate <= 0.50
        and controlled_ranking_quality >= 0.50
        and controlled_recovery_rate >= 1.00
    )
    holdout_validated = signal_validity["acceptance_gates"][
        "interaction_signal_validity_generalized"
    ]
    return _task_result(
        task_id="r6-research-task-false-alarm-control",
        product_values=["risk_distribution"],
        acceptance_decision=(
            "accepted_for_guarded_reporting"
            if current_proxy_control_passed and holdout_validated
            else "blocked_until_holdout_or_field_outcome"
        ),
        metrics={
            "baseline_false_alarm_rate": decision_value_metrics["summary"][
                "false_alarm_rate"
            ],
            "controlled_false_alarm_rate": controlled_false_alarm_rate,
            "controlled_risk_ranking_quality": controlled_ranking_quality,
            "controlled_static_prior_miss_recovery_rate": controlled_recovery_rate,
            "selected_source_keys": selected_source_keys,
        },
        acceptance_gates={
            "control_policy_present": True,
            "current_proxy_control_passed": current_proxy_control_passed,
            "holdout_validated": holdout_validated,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        source_artifact_ids=[
            decision_value_metrics["artifact_id"],
            signal_validity["artifact_id"],
        ],
    )


def _segment_outcome_labels_task(metrics: dict[str, Any]) -> dict[str, Any]:
    case_results = []
    total_predicted = 0
    total_true_positive = 0
    total_labeled = 0
    for case in metrics["case_results"]:
        predicted = [segment["segment_id"] for segment in case["top_abnormal_segments"]]
        labels = [
            segment["segment_id"]
            for segment in case["top_abnormal_segments"]
            if segment["delta_reject"] >= 0.06
        ]
        true_positive = len(set(predicted) & set(labels))
        total_predicted += len(predicted)
        total_labeled += len(labels)
        total_true_positive += true_positive
        case_results.append(
            {
                "source_key": case["source_key"],
                "predicted_segment_ids": predicted,
                "audit_label_segment_ids": labels,
                "true_positive_segment_count": true_positive,
            }
        )
    precision = _rate(total_true_positive, total_predicted)
    recall = _rate(total_true_positive, total_labeled)
    metrics_computable = total_predicted > 0 and total_labeled > 0
    return _task_result(
        task_id="r6-research-task-segment-outcome-labels",
        product_values=["abnormal_segments"],
        acceptance_decision=(
            "accepted_for_guarded_reporting"
            if metrics_computable
            else "blocked_until_holdout_or_field_outcome"
        ),
        metrics={
            "segment_precision": precision,
            "segment_recall": recall,
            "labeled_case_count": len(case_results),
            "label_source_type": "proxy_aligned_audit_fixture_not_field_outcome",
            "case_results": case_results,
        },
        acceptance_gates={
            "segment_label_protocol_present": True,
            "segment_metrics_computable": metrics_computable,
            "field_segment_labels_available": False,
            "product_claim_upgrade_allowed": False,
        },
        source_artifact_ids=[metrics["artifact_id"]],
    )


def _mechanism_holdout_validation_task(
    operator_holdout_validation: dict[str, Any],
) -> dict[str, Any]:
    summary = operator_holdout_validation["validation_summary"]
    gate = operator_holdout_validation["acceptance_gates"]
    return _task_result(
        task_id="r6-research-task-mechanism-holdout-validation",
        product_values=["mechanism_explanation"],
        acceptance_decision=(
            "accepted_for_guarded_reporting"
            if gate["operator_holdout_non_regression"]
            else "failed_current_public_proxy_gate"
        ),
        metrics={
            "operator_holdout_trial_count": summary["holdout_trial_count"],
            "operator_holdout_passed_trial_count": summary["passed_trial_count"],
            "failed_trial_count": summary["failed_trial_count"],
            "non_regression_trial_count": summary["non_regression_trial_count"],
        },
        acceptance_gates={
            "mechanism_holdout_validation_present": True,
            "operator_holdout_non_regression": gate["operator_holdout_non_regression"],
            "field_outcome_validated": gate["field_outcome_validated"],
            "runtime_default_allowed": gate["runtime_default_allowed"],
        },
        source_artifact_ids=[operator_holdout_validation["artifact_id"]],
    )


def _outcome_feedback_transfer_task(
    cross_case_transfer_protocol: dict[str, Any],
) -> dict[str, Any]:
    gates = cross_case_transfer_protocol["acceptance_gates"]
    return _task_result(
        task_id="r6-research-task-outcome-feedback-transfer",
        product_values=["outcome_feedback_learning"],
        acceptance_decision=(
            "accepted_for_guarded_reporting"
            if gates["runtime_update_guard_passed"]
            else "blocked_until_holdout_or_field_outcome"
        ),
        metrics={
            "outcome_feedback_transfer_available": gates[
                "outcome_feedback_transfer_available"
            ],
            "beats_prior_interaction_on_holdout": gates[
                "outcome_feedback_transfer_beats_prior_interaction"
            ],
            "beats_static_prior_on_holdout": gates[
                "outcome_feedback_transfer_beats_static_prior"
            ],
            "runtime_update_guard_passed": gates["runtime_update_guard_passed"],
            "global_update_accepted": gates["global_update_accepted"],
        },
        acceptance_gates={
            "outcome_feedback_transfer_available": gates[
                "outcome_feedback_transfer_available"
            ],
            "beats_prior_interaction_on_holdout": gates[
                "outcome_feedback_transfer_beats_prior_interaction"
            ],
            "runtime_update_guard_passed": gates["runtime_update_guard_passed"],
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        source_artifact_ids=[cross_case_transfer_protocol["artifact_id"]],
    )


def _task_result(
    *,
    task_id: str,
    product_values: list[str],
    acceptance_decision: str,
    metrics: dict[str, Any],
    acceptance_gates: dict[str, Any],
    source_artifact_ids: list[str],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "execution_status": "executed",
        "product_values": product_values,
        "acceptance_decision": acceptance_decision,
        "metrics": metrics,
        "acceptance_gates": acceptance_gates,
        "source_artifact_ids": source_artifact_ids,
        "claim_boundary": R6_CLAIM_BOUNDARY,
    }


def _execution_summary(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "task_count": len(task_results),
        "executed_task_count": sum(
            1 for task in task_results if task["execution_status"] == "executed"
        ),
        "accepted_for_guarded_reporting_count": sum(
            1
            for task in task_results
            if task["acceptance_decision"] == "accepted_for_guarded_reporting"
        ),
        "blocked_or_failed_count": sum(
            1
            for task in task_results
            if task["acceptance_decision"] != "accepted_for_guarded_reporting"
        ),
        "product_core_value_fully_supported": False,
    }


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def _unique_strings(values: Any) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = non_empty_string(value, field="source_refs")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_research_next_task_execution(
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
                "task_count": report["execution_summary"]["task_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
