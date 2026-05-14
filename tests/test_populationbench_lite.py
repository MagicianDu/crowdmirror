from benchmarks.populationbench_lite import build_populationbench_lite_spec


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
