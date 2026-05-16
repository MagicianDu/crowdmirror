from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


OBSERVED_FIELD = "observed_policy_reaction"
PREDICTED_FIELD = "predicted_policy_reaction"


def load_policy_reaction_records(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, list) or not payload:
        raise ValueError("policy reaction records must be a non-empty JSON list")
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise ValueError(f"policy reaction record {index} must be a JSON object")
    return payload


def compute_policy_reaction_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ValueError("policy reaction metrics require at least one record")

    jsd_values: list[float] = []
    correct_direction_count = 0
    segment_values: dict[str, dict[str, list[dict[str, float]]]] = {}
    source_ids: set[str] = set()
    provenance: set[str] = set()

    for record in records:
        record_id = str(record.get("record_id", "<missing-record-id>"))
        segment = _non_empty_string(record, "segment", record_id)
        source_ids.add(_non_empty_string(record, "source_id", record_id))
        if isinstance(record.get("provenance"), str) and record["provenance"]:
            provenance.add(record["provenance"])

        observed = _policy_distribution(record, OBSERVED_FIELD, record_id)
        predicted = _policy_distribution(record, PREDICTED_FIELD, record_id)
        jsd_values.append(_jsd(observed, predicted))

        true_ate = _finite_number(record, "true_ate", record_id)
        predicted_ate = _finite_number(record, "predicted_ate", record_id)
        if _direction(true_ate) == _direction(predicted_ate):
            correct_direction_count += 1

        by_segment = segment_values.setdefault(
            segment,
            {"observed": [], "predicted": []},
        )
        by_segment["observed"].append(observed)
        by_segment["predicted"].append(predicted)

    segment_correlations = {
        segment: _segment_rank_correlation(values["observed"], values["predicted"])
        for segment, values in segment_values.items()
    }
    metrics = {
        "record_count": len(records),
        "source_ids": sorted(source_ids),
        "provenance": sorted(provenance),
        "choice_distribution_jsd": _mean(jsd_values),
        "choice_distribution_jsd_record_count": len(jsd_values),
        "ate_direction_accuracy": correct_direction_count / len(records),
        "ate_direction_counts": {
            "correct": correct_direction_count,
            "total": len(records),
        },
        "segment_count": len(segment_correlations),
        "segment_rank_correlation": _mean(list(segment_correlations.values())),
        "worst_segment_rank_correlation": min(segment_correlations.values()),
        "segment_rank_correlation_by_segment": segment_correlations,
    }
    _assert_strict_json(metrics)
    return metrics


def _non_empty_string(record: dict[str, Any], field_name: str, record_id: str) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{record_id} missing non-empty {field_name}")
    return value


def _policy_distribution(
    record: dict[str, Any],
    field_name: str,
    record_id: str,
) -> dict[str, float]:
    raw = record.get(field_name)
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{record_id} missing non-empty {field_name}")
    values = {
        str(policy_id): _finite_probability(value, field_name, record_id)
        for policy_id, value in raw.items()
    }
    total = sum(values.values())
    if total <= 0:
        raise ValueError(f"{record_id} {field_name} must have positive mass")
    return {key: value / total for key, value in values.items()}


def _finite_probability(value: Any, field_name: str, record_id: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{record_id} {field_name} must contain numeric probabilities")
    probability = float(value)
    if not math.isfinite(probability) or probability < 0:
        raise ValueError(
            f"{record_id} {field_name} probabilities must be finite and non-negative"
        )
    return probability


def _finite_number(
    record: dict[str, Any],
    field_name: str,
    record_id: str,
) -> float:
    value = record.get(field_name)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{record_id} missing numeric {field_name}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{record_id} {field_name} must be finite")
    return number


def _jsd(observed: dict[str, float], predicted: dict[str, float]) -> float:
    policies = sorted(set(observed) | set(predicted))
    midpoint = {
        policy: (observed.get(policy, 0.0) + predicted.get(policy, 0.0)) / 2
        for policy in policies
    }
    return (_kl(observed, midpoint, policies) + _kl(predicted, midpoint, policies)) / 2


def _kl(
    distribution: dict[str, float],
    reference: dict[str, float],
    policies: list[str],
) -> float:
    divergence = 0.0
    for policy in policies:
        probability = distribution.get(policy, 0.0)
        if probability == 0:
            continue
        divergence += probability * math.log2(probability / reference[policy])
    return divergence


def _direction(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _segment_rank_correlation(
    observed_records: list[dict[str, float]],
    predicted_records: list[dict[str, float]],
) -> float:
    observed = _average_distribution(observed_records)
    predicted = _average_distribution(predicted_records)
    policies = sorted(set(observed) | set(predicted))
    if len(policies) < 2:
        raise ValueError("segment rank correlation requires at least two policies")
    observed_ranks = _ranks([observed.get(policy, 0.0) for policy in policies])
    predicted_ranks = _ranks([predicted.get(policy, 0.0) for policy in policies])
    return _pearson(observed_ranks, predicted_ranks)


def _average_distribution(records: list[dict[str, float]]) -> dict[str, float]:
    policies = sorted({policy for record in records for policy in record})
    return {
        policy: _mean([record.get(policy, 0.0) for record in records])
        for policy in policies
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


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)
