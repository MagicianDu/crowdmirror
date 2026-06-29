from __future__ import annotations

import json
import math
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
    benchmark_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    spec = build_populationbench_lite_spec()
    config = manifest.get("config", {})
    manifest_metrics = manifest.get("metrics", {})
    benchmark_metrics = (
        compute_populationbench_lite_metrics(benchmark_records)
        if benchmark_records is not None
        else {}
    )
    metrics = {**manifest_metrics, **benchmark_metrics}
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
        "benchmark_data": _benchmark_data_summary(benchmark_records),
        "benchmark_metrics": benchmark_metrics,
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
    benchmark_records: list[dict[str, Any]] | None = None,
) -> Path:
    payload = build_populationbench_lite_gate(
        manifest,
        artifact_id=artifact_id,
        benchmark_records=benchmark_records,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, allow_nan=False, indent=2, sort_keys=True))
    return output_path


def compute_populationbench_lite_metrics(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    if not records:
        raise ValueError("PopulationBench-lite metrics require at least one record")

    jsd_values: list[float] = []
    correct_direction_count = 0
    segment_values: dict[str, dict[str, list[dict[str, float]]]] = {}

    for record in records:
        record_id = str(record.get("record_id", "<missing-record-id>"))
        segment = record.get("segment")
        if not isinstance(segment, str) or not segment:
            raise ValueError(f"{record_id} missing non-empty segment")

        actual = _choice_share(record, "actual_choice_share", record_id)
        predicted = _choice_share(record, "predicted_choice_share", record_id)
        jsd_values.append(_jsd(actual, predicted))

        true_ate = _finite_number(record, "true_ate", record_id)
        predicted_ate = _finite_number(record, "predicted_ate", record_id)
        if _direction(true_ate) == _direction(predicted_ate):
            correct_direction_count += 1

        by_segment = segment_values.setdefault(
            segment,
            {"actual": [], "predicted": []},
        )
        by_segment["actual"].append(actual)
        by_segment["predicted"].append(predicted)

    segment_correlations = {
        segment: _segment_rank_correlation(values["actual"], values["predicted"])
        for segment, values in segment_values.items()
    }
    metric = {
        "choice_distribution_jsd": _mean(jsd_values),
        "choice_distribution_jsd_record_count": len(jsd_values),
        "ate_direction_accuracy": correct_direction_count / len(records),
        "ate_direction_counts": {
            "correct": correct_direction_count,
            "total": len(records),
        },
        "segment_rank_correlation": _mean(list(segment_correlations.values())),
        "worst_segment_rank_correlation": min(segment_correlations.values()),
        "segment_rank_correlation_by_segment": segment_correlations,
    }
    _assert_strict_json(metric)
    return metric


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


def _benchmark_data_summary(
    benchmark_records: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if benchmark_records is None:
        return {
            "status": "missing",
            "record_count": 0,
        }
    provenances = sorted(
        {
            record.get("provenance")
            for record in benchmark_records
            if isinstance(record.get("provenance"), str) and record.get("provenance")
        }
    )
    return {
        "status": "provided",
        "record_count": len(benchmark_records),
        "provenance": provenances,
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


def _choice_share(
    record: dict[str, Any],
    field_name: str,
    record_id: str,
) -> dict[str, float]:
    raw = record.get(field_name)
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{record_id} missing non-empty {field_name}")
    values = {
        str(alternative_id): _finite_probability(value, field_name, record_id)
        for alternative_id, value in raw.items()
    }
    total = sum(values.values())
    if total <= 0:
        raise ValueError(f"{record_id} {field_name} must have positive mass")
    return {key: value / total for key, value in values.items()}


def _finite_probability(value: Any, field_name: str, record_id: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{record_id} {field_name} must contain numeric probabilities")
    probability = float(value)
    if not math.isfinite(probability) or probability < 0:
        raise ValueError(f"{record_id} {field_name} probabilities must be finite and non-negative")
    return probability


def _finite_number(
    record: dict[str, Any],
    field_name: str,
    record_id: str,
) -> float:
    value = record.get(field_name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{record_id} missing numeric {field_name}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{record_id} {field_name} must be finite")
    return number


def _jsd(actual: dict[str, float], predicted: dict[str, float]) -> float:
    alternatives = sorted(set(actual) | set(predicted))
    midpoint = {
        alternative: (actual.get(alternative, 0.0) + predicted.get(alternative, 0.0)) / 2
        for alternative in alternatives
    }
    return (
        _kl(actual, midpoint, alternatives) + _kl(predicted, midpoint, alternatives)
    ) / 2


def _kl(
    distribution: dict[str, float],
    reference: dict[str, float],
    alternatives: list[str],
) -> float:
    divergence = 0.0
    for alternative in alternatives:
        probability = distribution.get(alternative, 0.0)
        if probability == 0:
            continue
        divergence += probability * math.log2(probability / reference[alternative])
    return divergence


def _direction(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _segment_rank_correlation(
    actual_records: list[dict[str, float]],
    predicted_records: list[dict[str, float]],
) -> float:
    actual = _average_choice_share(actual_records)
    predicted = _average_choice_share(predicted_records)
    alternatives = sorted(set(actual) | set(predicted))
    if len(alternatives) < 2:
        raise ValueError("segment rank correlation requires at least two alternatives")
    actual_ranks = _ranks([actual.get(alternative, 0.0) for alternative in alternatives])
    predicted_ranks = _ranks([
        predicted.get(alternative, 0.0) for alternative in alternatives
    ])
    return _pearson(actual_ranks, predicted_ranks)


def _average_choice_share(records: list[dict[str, float]]) -> dict[str, float]:
    alternatives = sorted({alternative for record in records for alternative in record})
    return {
        alternative: _mean([record.get(alternative, 0.0) for record in records])
        for alternative in alternatives
    }


def _ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0 for _ in values]
    position = 0
    while position < len(ordered):
        end = position + 1
        while end < len(ordered) and ordered[end][1] == ordered[position][1]:
            end += 1
        average_rank = (position + 1 + end) / 2
        for index, _ in ordered[position:end]:
            ranks[index] = average_rank
        position = end
    return ranks


def _pearson(left: list[float], right: list[float]) -> float:
    left_mean = _mean(left)
    right_mean = _mean(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right)
    )
    left_variance = sum((value - left_mean) ** 2 for value in left)
    right_variance = sum((value - right_mean) ** 2 for value in right)
    denominator = math.sqrt(left_variance * right_variance)
    if denominator == 0:
        return 1.0 if left == right else 0.0
    return numerator / denominator


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)
