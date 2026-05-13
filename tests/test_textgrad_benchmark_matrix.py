from experiments.textgrad_benchmark_matrix import build_matrix_plan, summarize_matrix


def test_build_matrix_plan_contains_required_runs():
    plan = build_matrix_plan(run_prefix="matrix-test")
    run_ids = [case["run_id"] for case in plan]
    assert "matrix-test-dry-eval1-baseline" in run_ids
    assert "matrix-test-local-eval1-limited" in run_ids
    assert all(case["eval_size"] in {1, 2, 5} for case in plan)
    assert all(case["max_iterations"] >= 2 for case in plan)


def test_summarize_matrix_marks_negative_textgrad_result():
    summary = summarize_matrix(
        [
            {
                "run_id": "local-a",
                "mode": "local",
                "metrics": {
                    "initial_loss": 0.036,
                    "best_loss": 0.036,
                    "improvement_ratio": 0.0,
                    "textgrad_call_count": 2,
                    "prompt_update_count": 2,
                },
            }
        ]
    )
    assert summary["best_improvement_ratio"] == 0.0
    assert summary["negative_result_count"] == 1
