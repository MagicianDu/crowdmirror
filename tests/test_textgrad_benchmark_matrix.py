from experiments.textgrad_benchmark_matrix import (
    build_paper_gate_plan,
    build_matrix_plan,
    classify_paper_gate_manifest,
    diagnose_manifest,
    evaluate_paper_gate,
    summarize_paper_gate_evidence,
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


def test_summarize_matrix_reports_candidate_acceptance_counts():
    summary = summarize_matrix(
        [
            {
                "run_id": "local-a",
                "metrics": {
                    "initial_loss": 0.30,
                    "best_loss": 0.20,
                    "final_loss": 0.22,
                    "improvement_ratio": 0.33,
                    "candidate_update_count": 2,
                    "candidate_evaluated_count": 2,
                    "candidate_accepted_count": 1,
                    "candidate_rejected_count": 1,
                    "candidate_pending_count": 0,
                    "candidate_acceptance_rate": 0.5,
                },
            },
            {
                "run_id": "local-b",
                "metrics": {
                    "initial_loss": 0.40,
                    "best_loss": 0.40,
                    "final_loss": 0.50,
                    "improvement_ratio": 0.0,
                    "candidate_update_count": 1,
                    "candidate_evaluated_count": 0,
                    "candidate_accepted_count": 0,
                    "candidate_rejected_count": 0,
                    "candidate_pending_count": 1,
                    "candidate_acceptance_rate": None,
                },
            },
        ]
    )

    assert summary["candidate_update_count"] == 3
    assert summary["candidate_evaluated_count"] == 2
    assert summary["candidate_accepted_count"] == 1
    assert summary["candidate_rejected_count"] == 1
    assert summary["candidate_pending_count"] == 1
    assert summary["candidate_acceptance_rate"] == 0.5


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


def test_build_paper_gate_plan_requires_eval5_seeds_repeats_and_comparison_axes():
    plan = build_paper_gate_plan(
        run_prefix="paper",
        dataset_seeds=(42, 7, 99),
        prompt_baselines=("default", "compact"),
        textgrad_token_budgets=(1024, 2048),
        repeats=2,
    )

    assert len(plan) == 3 * 2 * 2 * 2
    assert all(case["eval_size"] == 5 for case in plan)
    assert {case["dataset_seed"] for case in plan} == {42, 7, 99}
    assert {case["prompt_baseline"] for case in plan} == {"default", "compact"}
    assert {case["textgrad_max_tokens"] for case in plan} == {1024, 2048}
    assert {case["repeat"] for case in plan} == {1, 2}
    assert "paper-local-seed42-eval5-default-tg2048-r2" in {
        case["run_id"] for case in plan
    }


def test_evaluate_paper_gate_reports_insufficient_evidence_until_matrix_complete():
    gate = evaluate_paper_gate(
        [
            {
                "run_id": "paper-local-seed42-eval5-default-tg2048-r1",
                "config": {
                    "eval_size": 5,
                    "dataset_seed": 42,
                    "prompt_baseline": "default",
                    "textgrad_max_tokens": 2048,
                    "repeat": 1,
                },
                "metrics": {
                    "improvement_ratio": 0.2,
                    "textgrad_effect_status": "improved",
                },
            }
        ],
        required_seeds=(42, 7, 99),
        required_prompt_baselines=("default", "compact"),
        required_textgrad_token_budgets=(1024, 2048),
        required_repeats=2,
    )

    assert gate["status"] == "insufficient_evidence"
    assert gate["observed_run_count"] == 1
    assert gate["required_run_count"] == 24
    assert "missing_seed:7" in gate["missing_cells"]
    assert "missing_seed:42" not in gate["missing_cells"]


def test_evaluate_paper_gate_infers_repeat_from_run_id_when_config_omits_it():
    manifests = [
        {
            "run_id": "paper-local-seed42-eval5-compact-tg1024-r1",
            "config": {
                "eval_size": 5,
                "dataset_seed": 42,
                "prompt_baseline": "compact",
                "textgrad_max_tokens": 1024,
            },
            "metrics": {
                "improvement_ratio": 0.1,
                "textgrad_effect_status": "improved",
            },
        },
        {
            "run_id": "paper-local-seed42-eval5-compact-tg1024-r2",
            "config": {
                "eval_size": 5,
                "dataset_seed": 42,
                "prompt_baseline": "compact",
                "textgrad_max_tokens": 1024,
            },
            "metrics": {
                "improvement_ratio": 0.1,
                "textgrad_effect_status": "improved",
            },
        },
    ]

    gate = evaluate_paper_gate(
        manifests,
        required_seeds=(42,),
        required_prompt_baselines=("compact",),
        required_textgrad_token_budgets=(1024,),
        required_repeats=2,
    )

    assert gate["status"] == "passed"
    assert gate["observed_run_count"] == 2


def test_evaluate_paper_gate_prefers_repeat_from_run_id_over_stale_config():
    manifests = [
        {
            "run_id": "paper-local-seed42-eval5-compact-tg1024-r2",
            "config": {
                "eval_size": 5,
                "dataset_seed": 42,
                "prompt_baseline": "compact",
                "textgrad_max_tokens": 1024,
                "repeat": 1,
            },
            "metrics": {
                "improvement_ratio": 0.1,
                "textgrad_effect_status": "improved",
            },
        },
    ]

    gate = evaluate_paper_gate(
        manifests,
        required_seeds=(42,),
        required_prompt_baselines=("compact",),
        required_textgrad_token_budgets=(1024,),
        required_repeats=2,
    )

    assert gate["observed_run_count"] == 1
    assert "missing_cell:seed42:compact:tg1024:r1" in gate["missing_cells"]
    assert "missing_cell:seed42:compact:tg1024:r2" not in gate["missing_cells"]


def test_evaluate_paper_gate_passes_when_required_cells_improve():
    manifests = []
    for seed in (42, 7, 99):
        for prompt_baseline in ("default", "compact"):
            for budget in (1024, 2048):
                for repeat in (1, 2):
                    manifests.append(
                        {
                            "run_id": (
                                f"paper-local-seed{seed}-eval5-"
                                f"{prompt_baseline}-tg{budget}-r{repeat}"
                            ),
                            "config": {
                                "eval_size": 5,
                                "dataset_seed": seed,
                                "prompt_baseline": prompt_baseline,
                                "textgrad_max_tokens": budget,
                                "repeat": repeat,
                            },
                            "metrics": {
                                "improvement_ratio": 0.1,
                                "textgrad_effect_status": "improved",
                            },
                        }
                    )

    gate = evaluate_paper_gate(
        manifests,
        required_seeds=(42, 7, 99),
        required_prompt_baselines=("default", "compact"),
        required_textgrad_token_budgets=(1024, 2048),
        required_repeats=2,
    )

    assert gate["status"] == "passed"
    assert gate["improved_run_count"] == 24
    assert gate["negative_result_count"] == 0


def test_classify_paper_gate_manifest_marks_v2_and_legacy_pending_evidence():
    assert classify_paper_gate_manifest(
        {
            "run_id": "textgrad-paper-gate-v2-local-seed42-eval5-default-tg1024-r2",
            "metrics": {"candidate_pending_count": 0},
        }
    ) == {"evidence_generation": "current_v2", "legacy": False}

    assert classify_paper_gate_manifest(
        {
            "run_id": "textgrad-paper-gate-local-seed42-eval5-default-tg1024-r1",
            "metrics": {"candidate_pending_count": 1},
        }
    ) == {
        "evidence_generation": "legacy_pending_candidate_evidence",
        "legacy": True,
    }


def test_summarize_paper_gate_evidence_exposes_claim_boundaries_and_axes():
    manifests = [
        {
            "run_id": "textgrad-paper-gate-local-seed42-eval5-default-tg1024-r1",
            "config": {
                "eval_size": 5,
                "dataset_seed": 42,
                "prompt_baseline": "default",
                "textgrad_max_tokens": 1024,
                "repeat": 1,
            },
            "metrics": {
                "improvement_ratio": 0.2,
                "textgrad_effect_status": "improved",
                "candidate_update_count": 1,
                "candidate_evaluated_count": 0,
                "candidate_accepted_count": 0,
                "candidate_rejected_count": 0,
                "candidate_pending_count": 1,
            },
        },
        {
            "run_id": "textgrad-paper-gate-v2-local-seed42-eval5-default-tg1024-r2",
            "config": {
                "eval_size": 5,
                "dataset_seed": 42,
                "prompt_baseline": "default",
                "textgrad_max_tokens": 1024,
                "repeat": 2,
            },
            "metrics": {
                "improvement_ratio": 0.0,
                "textgrad_effect_status": "updated_no_improvement",
                "candidate_update_count": 1,
                "candidate_evaluated_count": 1,
                "candidate_accepted_count": 0,
                "candidate_rejected_count": 1,
                "candidate_pending_count": 0,
            },
        },
        {
            "run_id": "textgrad-paper-gate-v2-local-seed42-eval5-default-tg1024-r3",
            "config": {
                "eval_size": 5,
                "dataset_seed": 42,
                "prompt_baseline": "default",
                "textgrad_max_tokens": 1024,
                "repeat": 3,
            },
            "metrics": {
                "improvement_ratio": 0.1,
                "textgrad_effect_status": "improved",
                "candidate_update_count": 1,
                "candidate_evaluated_count": 1,
                "candidate_accepted_count": 1,
                "candidate_rejected_count": 0,
                "candidate_pending_count": 0,
            },
        },
    ]

    summary = summarize_paper_gate_evidence(
        manifests,
        required_seeds=(42,),
        required_prompt_baselines=("default",),
        required_textgrad_token_budgets=(1024,),
    )

    assert summary["schema_version"] == "circe-textgrad-paper-gate-v2"
    assert summary["paper_gate"]["status"] == "failed"
    assert summary["paper_conclusion"] == "coverage_complete_textgrad_unstable"
    assert summary["evidence_generation_counts"] == {
        "current_v2": 2,
        "legacy_pending_candidate_evidence": 1,
    }
    assert summary["baseline_summaries"]["default"]["run_count"] == 3
    assert summary["token_budget_summaries"]["1024"]["negative_result_count"] == 1
    assert summary["seed_summaries"]["42"]["candidate_rejected_count"] == 1
    assert any("legacy runs contain pending" in boundary for boundary in summary["claim_boundaries"])
