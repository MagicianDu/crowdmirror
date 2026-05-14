from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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


def build_populationbench_lite_gate(
    manifest: dict[str, Any],
    *,
    artifact_id: str = "populationbench-lite-smoke-001",
) -> dict[str, Any]:
    spec = build_populationbench_lite_spec()
    config = manifest.get("config", {})
    metrics = manifest.get("metrics", {})
    tasks = [
        _metric_task(
            task_id="distributional_choice_fit",
            metric="choice_distribution_jsd",
            metrics=metrics,
        ),
        _metric_task(
            task_id="counterfactual_direction",
            metric="ate_direction_accuracy",
            metrics=metrics,
        ),
        _metric_task(
            task_id="segment_stability",
            metric="segment_rank_correlation",
            metrics=metrics,
        ),
        _auditability_task(config=config, metrics=metrics),
    ]
    overall_status = (
        "passed" if all(task["status"] == "passed" for task in tasks)
        else "blocked_for_paper_claim"
    )
    payload = {
        "schema_version": spec["benchmark_id"],
        "artifact_id": artifact_id,
        "source_run_id": manifest.get("run_id"),
        "overall_status": overall_status,
        "evidence_axes": {
            "seed": config.get("dataset_seed"),
            "model": config.get("model"),
            "prompt_baseline": config.get("prompt_baseline"),
        },
        "tasks": tasks,
        "claim_boundary": (
            "PopulationBench-lite smoke gate checks reproducible local evidence readiness; "
            "it is not field validation."
        ),
    }
    _assert_strict_json(payload)
    return payload


def write_populationbench_lite_gate(
    path: str | Path,
    *,
    manifest: dict[str, Any],
    artifact_id: str = "populationbench-lite-smoke-001",
) -> Path:
    payload = build_populationbench_lite_gate(
        manifest,
        artifact_id=artifact_id,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, allow_nan=False, indent=2, sort_keys=True))
    return output_path


def _metric_task(
    *,
    task_id: str,
    metric: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    if metric not in metrics:
        return {
            "task_id": task_id,
            "metric": metric,
            "status": "blocked",
            "reason": f"{metric}_not_recorded",
        }
    return {
        "task_id": task_id,
        "metric": metric,
        "status": "passed",
        "value": metrics[metric],
    }


def _auditability_task(
    *,
    config: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    required_config = {
        "dataset_seed": "seed",
        "model": "model",
        "prompt_baseline": "prompt_baseline",
    }
    required_metrics = (
        "initial_loss",
        "best_loss",
        "final_loss",
        "candidate_update_policy",
        "candidate_update_count",
        "candidate_evaluated_count",
        "candidate_accepted_count",
        "candidate_rejected_count",
        "candidate_pending_count",
    )
    missing = [
        label
        for field, label in required_config.items()
        if field not in config
    ]
    missing.extend(
        field for field in required_metrics if field not in metrics
    )
    status = "passed" if not missing else "failed"
    return {
        "task_id": "auditability",
        "metric": "strict_json_manifest_completeness",
        "status": status,
        "missing_fields": missing,
    }


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)
