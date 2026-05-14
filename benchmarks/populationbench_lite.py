from __future__ import annotations


EVIDENCE_REQUIRED = [
    "seed",
    "model",
    "prompt_baseline",
    "acceptance_gate_fields",
]


def build_populationbench_lite_spec() -> dict:
    return {
        "benchmark_id": "populationbench-lite-v0",
        "claim_boundary": (
            "benchmark defines reproducible local evidence; it is not field validation"
        ),
        "tasks": [
            {
                "task_id": "distributional_choice_fit",
                "metric": "choice_distribution_jsd",
                "pass_rule": "lower_is_better_report_confidence_interval",
                "evidence_required": EVIDENCE_REQUIRED,
            },
            {
                "task_id": "counterfactual_direction",
                "metric": "ate_direction_accuracy",
                "pass_rule": "report_accuracy_by_seed_and_prompt_baseline",
                "evidence_required": EVIDENCE_REQUIRED,
            },
            {
                "task_id": "segment_stability",
                "metric": "segment_rank_correlation",
                "pass_rule": "report_mean_and_worst_segment",
                "evidence_required": EVIDENCE_REQUIRED,
            },
            {
                "task_id": "auditability",
                "metric": "strict_json_manifest_completeness",
                "pass_rule": (
                    "all_runs_have_seed_model_prompt_and_acceptance_gate_fields"
                ),
                "evidence_required": EVIDENCE_REQUIRED,
            },
        ],
    }
