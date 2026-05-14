import json
from pathlib import Path

from benchmarks.populationbench_lite import (
    build_populationbench_lite_gate,
    build_populationbench_lite_spec,
    compute_populationbench_lite_metrics,
    write_populationbench_lite_gate,
)


def test_populationbench_lite_spec_has_reviewer_facing_tasks():
    spec = build_populationbench_lite_spec()
    task_ids = {task["task_id"] for task in spec["tasks"]}

    assert spec["benchmark_id"] == "populationbench-lite-v0"
    assert task_ids == {
        "distributional_choice_fit",
        "counterfactual_direction",
        "segment_stability",
        "auditability",
    }
    assert spec["claim_boundary"] == (
        "benchmark defines reproducible local evidence; it is not field validation"
    )


def test_populationbench_lite_tasks_define_metrics_and_pass_rules():
    spec = build_populationbench_lite_spec()

    for task in spec["tasks"]:
        assert task["metric"]
        assert task["pass_rule"]
        assert task["evidence_required"] == [
            "seed",
            "model",
            "prompt_baseline",
            "acceptance_gate_fields",
        ]


def test_populationbench_lite_gate_marks_auditability_and_metric_gaps():
    gate = build_populationbench_lite_gate(_acceptance_gated_manifest())

    assert gate["schema_version"] == "populationbench-lite-v0"
    assert gate["artifact_id"] == "populationbench-lite-smoke-001"
    assert gate["overall_status"] == "blocked_for_paper_claim"
    task_status = {
        task["task_id"]: task["status"]
        for task in gate["tasks"]
    }
    assert task_status == {
        "distributional_choice_fit": "blocked",
        "counterfactual_direction": "blocked",
        "segment_stability": "blocked",
        "auditability": "passed",
    }
    assert gate["evidence_axes"] == {
        "seed": 42,
        "model": "google/gemma-4-31b",
        "prompt_baseline": "default",
    }
    assert gate["claim_boundary"] == (
        "PopulationBench-lite smoke gate checks reproducible local evidence readiness; "
        "it is not field validation."
    )


def test_populationbench_lite_metrics_are_computed_from_records():
    metrics = compute_populationbench_lite_metrics(_benchmark_records())

    assert 0 < metrics["choice_distribution_jsd"] < 0.02
    assert metrics["choice_distribution_jsd_record_count"] == 2
    assert metrics["ate_direction_accuracy"] == 1.0
    assert metrics["ate_direction_counts"] == {"correct": 2, "total": 2}
    assert metrics["segment_rank_correlation"] == 1.0
    assert metrics["worst_segment_rank_correlation"] == 1.0
    assert metrics["segment_rank_correlation_by_segment"] == {
        "budget": 1.0,
        "premium": 1.0,
    }


def test_populationbench_lite_gate_passes_when_metrics_are_computed_from_records():
    gate = build_populationbench_lite_gate(
        _acceptance_gated_manifest(),
        benchmark_records=_benchmark_records(),
    )

    assert gate["overall_status"] == "passed"
    task_status = {
        task["task_id"]: task["status"]
        for task in gate["tasks"]
    }
    assert task_status == {
        "distributional_choice_fit": "passed",
        "counterfactual_direction": "passed",
        "segment_stability": "passed",
        "auditability": "passed",
    }
    assert gate["benchmark_data"] == {
        "status": "provided",
        "record_count": 2,
        "provenance": ["synthetic_populationbench_lite_smoke_fixture"],
    }
    assert gate["benchmark_metrics"]["ate_direction_accuracy"] == 1.0


def test_write_populationbench_lite_gate_writes_strict_json(tmp_path):
    path = tmp_path / "populationbench-lite-smoke.json"

    written_path = write_populationbench_lite_gate(
        path,
        manifest=_acceptance_gated_manifest(),
        artifact_id="populationbench-lite-test",
        benchmark_records=_benchmark_records(),
    )

    assert written_path == path
    payload = json.loads(path.read_text())
    assert payload["artifact_id"] == "populationbench-lite-test"
    assert payload["tasks"][-1]["task_id"] == "auditability"
    assert payload["overall_status"] == "passed"


def _acceptance_gated_manifest() -> dict:
    return {
        "run_id": "textgrad-paper-gate-v3-smoke-local-seed42-eval5-default-tg2048-r1",
        "config": {
            "dataset_seed": 42,
            "model": "google/gemma-4-31b",
            "prompt_baseline": "default",
        },
        "metrics": {
            "initial_loss": 0.4263471921660694,
            "best_loss": 0.13398698685605823,
            "final_loss": 0.13398698685605823,
            "candidate_update_policy": "accept_if_loss_improves_else_revert",
            "candidate_update_count": 1,
            "candidate_evaluated_count": 1,
            "candidate_accepted_count": 1,
            "candidate_rejected_count": 0,
            "candidate_pending_count": 0,
        },
    }


def _benchmark_records() -> list[dict]:
    return json.loads(
        Path("benchmarks/fixtures/populationbench_lite_smoke_records.json").read_text()
    )
