from experiments.textgrad_benchmark_matrix import (
    build_matrix_plan,
    diagnose_manifest,
    summarize_matrix,
)


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


def test_build_matrix_plan_expands_seed_prompt_and_budget_axes():
    plan = build_matrix_plan(
        run_prefix="diag",
        eval_sizes=(1, 2),
        dataset_seeds=(42, 7),
        prompt_baselines=("default", "compact"),
        textgrad_token_budgets=(1024, 2048),
        modes=("local",),
    )
    run_ids = {case["run_id"] for case in plan}

    assert "diag-local-seed42-eval2-compact-tg2048" in run_ids
    assert "diag-local-seed7-eval1-default-tg1024" in run_ids
    assert all(case["dataset_seed"] in {42, 7} for case in plan)
    assert all(case["prompt_baseline"] in {"default", "compact"} for case in plan)
    assert all(case["textgrad_max_tokens"] in {1024, 2048} for case in plan)


def test_diagnose_manifest_flags_small_eval_truncation_and_budget_saturation():
    diagnosis = diagnose_manifest(
        {
            "config": {
                "eval_size": 1,
                "textgrad_max_tokens": 1024,
            },
            "metrics": {
                "improvement_ratio": 0.0,
                "textgrad_call_count": 2,
                "prompt_update_count": 2,
                "textgrad_output_tokens": 2048,
                "suspected_prompt_truncation_count": 1,
                "textgrad_effect_status": "updated_no_improvement",
            },
        }
    )

    assert diagnosis["flags"] == [
        "eval_size_too_small_to_judge",
        "textgrad_output_budget_saturated",
        "suspected_prompt_truncation",
    ]
    assert diagnosis["primary_hypothesis"] == "textgrad_output_budget_saturated"


def test_summarize_matrix_counts_diagnosis_flags():
    summary = summarize_matrix(
        [
            {
                "config": {"eval_size": 1, "textgrad_max_tokens": 1024},
                "metrics": {
                    "improvement_ratio": 0.0,
                    "textgrad_call_count": 2,
                    "prompt_update_count": 2,
                    "textgrad_output_tokens": 2048,
                    "suspected_prompt_truncation_count": 1,
                    "textgrad_effect_status": "updated_no_improvement",
                },
            }
        ]
    )

    assert summary["diagnosis_counts"] == {
        "eval_size_too_small_to_judge": 1,
        "suspected_prompt_truncation": 1,
        "textgrad_output_budget_saturated": 1,
    }
