import json
import subprocess
import sys

from experiments.r6_research_next_task_execution import (
    build_r6_research_next_task_execution,
)


def test_r6_research_next_task_execution_runs_all_five_tasks():
    report = build_r6_research_next_task_execution(
        artifact_id="r6-research-next-task-execution-test",
        run_id="r6-next-task-run",
    )

    assert report["schema_version"] == "r6-research-next-task-execution-v1"
    assert report["status"] == "research_next_tasks_executed_with_guarded_results"
    assert report["acceptance_gates"] == {
        "all_five_tasks_executed": True,
        "all_task_results_have_source_refs": True,
        "all_task_results_have_acceptance_decision": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "product_core_value_fully_supported": False,
    }
    assert [task["task_id"] for task in report["task_results"]] == [
        "r6-research-task-trend-interval-holdout",
        "r6-research-task-false-alarm-control",
        "r6-research-task-segment-outcome-labels",
        "r6-research-task-mechanism-holdout-validation",
        "r6-research-task-outcome-feedback-transfer",
    ]
    for task in report["task_results"]:
        assert task["execution_status"] == "executed"
        assert task["acceptance_decision"] in {
            "accepted_for_guarded_reporting",
            "blocked_until_holdout_or_field_outcome",
            "failed_current_public_proxy_gate",
        }
        assert task["source_artifact_ids"]
        assert task["product_values"]
        assert task["claim_boundary"]
    json.dumps(report, allow_nan=False)


def test_r6_research_next_task_execution_reports_task_specific_results():
    report = build_r6_research_next_task_execution(
        artifact_id="r6-research-next-task-execution-test",
        run_id="r6-next-task-run",
    )
    tasks = {task["task_id"]: task for task in report["task_results"]}

    trend = tasks["r6-research-task-trend-interval-holdout"]
    assert trend["metrics"]["trend_direction_accuracy"] == 0.667
    assert trend["metrics"]["interval_coverage"] == 0.667
    assert trend["acceptance_decision"] == "failed_current_public_proxy_gate"

    false_alarm = tasks["r6-research-task-false-alarm-control"]
    assert false_alarm["metrics"]["baseline_false_alarm_rate"] == 0.667
    assert false_alarm["metrics"]["controlled_false_alarm_rate"] == 0.0
    assert false_alarm["metrics"]["controlled_risk_ranking_quality"] == 1.0
    assert false_alarm["acceptance_gates"]["current_proxy_control_passed"] is True
    assert false_alarm["acceptance_gates"]["holdout_validated"] is False
    assert false_alarm["acceptance_decision"] == "blocked_until_holdout_or_field_outcome"

    segment = tasks["r6-research-task-segment-outcome-labels"]
    assert segment["acceptance_gates"]["segment_label_protocol_present"] is True
    assert segment["acceptance_gates"]["segment_metrics_computable"] is True
    assert segment["acceptance_gates"]["field_segment_labels_available"] is False
    assert segment["metrics"]["segment_precision"] == 0.667
    assert segment["metrics"]["segment_recall"] == 1.0

    mechanism = tasks["r6-research-task-mechanism-holdout-validation"]
    assert mechanism["metrics"]["operator_holdout_passed_trial_count"] == 0
    assert mechanism["acceptance_gates"]["operator_holdout_non_regression"] is False
    assert mechanism["acceptance_decision"] == "failed_current_public_proxy_gate"

    transfer = tasks["r6-research-task-outcome-feedback-transfer"]
    assert transfer["acceptance_gates"]["outcome_feedback_transfer_available"] is True
    assert transfer["acceptance_gates"]["beats_prior_interaction_on_holdout"] is True
    assert transfer["acceptance_gates"]["runtime_update_guard_passed"] is False
    assert transfer["acceptance_decision"] == "blocked_until_holdout_or_field_outcome"


def test_r6_research_next_task_execution_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-research-next-task-execution.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_research_next_task_execution.py",
            "--artifact-id",
            "r6-research-next-task-execution-cli",
            "--run-id",
            "r6-next-task-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r6-research-next-task-execution-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-research-next-task-execution-cli",
        "output": str(output),
        "status": "research_next_tasks_executed_with_guarded_results",
        "task_count": 5,
    }
