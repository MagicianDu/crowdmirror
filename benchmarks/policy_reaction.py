from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


OBSERVED_FIELD = "observed_policy_reaction"
PREDICTED_FIELD = "predicted_policy_reaction"
POLICY_IDS = (
    "baseline_no_new_support",
    "food_subsidy_expansion",
    "cash_cost_of_living_rebate",
)
HPS_PUBLIC_ROW_REQUIRED_FIELDS = (
    "record_id",
    "household_has_children",
    "household_income_bracket",
    "employment_status",
    "FD1_food_sufficiency_last_7_days",
    "FD2_child_recent_food_insufficiency_unaffordable_last_7_days",
    "SPN4_difficulty_paying_usual_household_expenses_last_2_months",
    "INFLATE2_stress_from_price_increases_last_2_months",
    "EMP1_household_loss_employment_income_last_4_weeks",
    "predicted_baseline_no_new_support",
    "predicted_food_subsidy_expansion",
    "predicted_cash_cost_of_living_rebate",
)


def load_policy_reaction_records(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, list) or not payload:
        raise ValueError("policy reaction records must be a non-empty JSON list")
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise ValueError(f"policy reaction record {index} must be a JSON object")
    return payload


def load_hps_public_rows(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if input_path.suffix.lower() == ".csv":
        with input_path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        rows = json.loads(input_path.read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError("HPS public rows must be a non-empty list")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"HPS public row {index} must be an object")
        _validate_hps_public_row(row, index)
    return rows


def build_policy_reaction_records_from_hps_rows(
    rows: list[dict[str, Any]],
    *,
    source_id: str = "hps_htops_food_cost_core",
    provenance: str = "hps_htops_public_row_converter_smoke_fixture",
) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("HPS public rows must be non-empty")

    records = []
    for index, row in enumerate(rows):
        _validate_hps_public_row(row, index)
        record_id = _row_string(row, "record_id", index)
        observed = _observed_policy_reaction_from_hps_row(row)
        predicted = _predicted_policy_reaction_from_hps_row(row, record_id)
        records.append(
            {
                "record_id": record_id,
                "source_id": source_id,
                "segment": _segment_from_hps_row(row),
                OBSERVED_FIELD: observed,
                PREDICTED_FIELD: predicted,
                "true_ate": _support_lift(observed),
                "predicted_ate": _support_lift(predicted),
                "provenance": provenance,
            }
        )
    return records


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


def _validate_hps_public_row(row: dict[str, Any], index: int) -> None:
    missing = [
        field
        for field in HPS_PUBLIC_ROW_REQUIRED_FIELDS
        if field not in row or row[field] in (None, "")
    ]
    if missing:
        raise ValueError(f"HPS public row {index} missing fields: {', '.join(missing)}")


def _observed_policy_reaction_from_hps_row(
    row: dict[str, Any],
) -> dict[str, float]:
    food_stress = _max_score(
        _food_sufficiency_score(row["FD1_food_sufficiency_last_7_days"]),
        _child_food_score(
            row["FD2_child_recent_food_insufficiency_unaffordable_last_7_days"]
        ),
    )
    child_food_stress = _child_food_score(
        row["FD2_child_recent_food_insufficiency_unaffordable_last_7_days"]
    )
    expense_stress = _expense_difficulty_score(
        row["SPN4_difficulty_paying_usual_household_expenses_last_2_months"]
    )
    inflation_stress = _inflation_stress_score(
        row["INFLATE2_stress_from_price_increases_last_2_months"]
    )
    price_stress = _max_score(expense_stress, inflation_stress)
    income_loss = _yes_no_score(
        row["EMP1_household_loss_employment_income_last_4_weeks"]
    )

    baseline_score = max(0.25, 2.5 - 1.25 * _max_score(food_stress, price_stress))
    baseline_score -= 0.35 * income_loss
    baseline_score = max(0.25, baseline_score)
    scores = {
        "baseline_no_new_support": baseline_score,
        "food_subsidy_expansion": 0.5 + 4.0 * food_stress + 1.5 * child_food_stress,
        "cash_cost_of_living_rebate": (
            0.5 + 1.8 * price_stress + 0.5 * expense_stress + 0.3 * income_loss
        ),
    }
    return _normalize_scores(scores)


def _predicted_policy_reaction_from_hps_row(
    row: dict[str, Any],
    record_id: str,
) -> dict[str, float]:
    distribution = {
        "baseline_no_new_support": _finite_probability(
            _parse_float(row["predicted_baseline_no_new_support"]),
            PREDICTED_FIELD,
            record_id,
        ),
        "food_subsidy_expansion": _finite_probability(
            _parse_float(row["predicted_food_subsidy_expansion"]),
            PREDICTED_FIELD,
            record_id,
        ),
        "cash_cost_of_living_rebate": _finite_probability(
            _parse_float(row["predicted_cash_cost_of_living_rebate"]),
            PREDICTED_FIELD,
            record_id,
        ),
    }
    return _normalize_scores(distribution)


def _segment_from_hps_row(row: dict[str, Any]) -> str:
    income = str(row["household_income_bracket"]).lower()
    food_stress = _food_sufficiency_score(row["FD1_food_sufficiency_last_7_days"])
    price_stress = _max_score(
        _expense_difficulty_score(
            row["SPN4_difficulty_paying_usual_household_expenses_last_2_months"]
        ),
        _inflation_stress_score(
            row["INFLATE2_stress_from_price_increases_last_2_months"]
        ),
    )
    employment_status = str(row["employment_status"]).lower()
    has_children = _yes_no_score(row["household_has_children"]) > 0

    if "less_than_25000" in income and food_stress >= 0.5:
        return "low_income_food_insecure"
    if has_children and price_stress >= 0.6:
        return "working_family_price_stressed"
    if employment_status in {"retired", "not_in_labor_force"} and price_stress >= 0.6:
        return "fixed_income_inflation_stressed"
    return "general_population_cost_pressure"


def _support_lift(distribution: dict[str, float]) -> float:
    return (
        distribution["food_subsidy_expansion"]
        + distribution["cash_cost_of_living_rebate"]
        - distribution["baseline_no_new_support"]
    )


def _row_string(row: dict[str, Any], field_name: str, index: int) -> str:
    value = row.get(field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"HPS public row {index} missing {field_name}")
    return value


def _food_sufficiency_score(value: Any) -> float:
    return _categorical_score(
        value,
        {
            "1": 0.0,
            "enough_of_kinds_wanted": 0.0,
            "food_sufficient": 0.0,
            "2": 0.25,
            "enough_but_not_always_kinds_wanted": 0.25,
            "3": 0.75,
            "sometimes_not_enough": 0.75,
            "4": 1.0,
            "often_not_enough": 1.0,
        },
        field_name="FD1_food_sufficiency_last_7_days",
    )


def _child_food_score(value: Any) -> float:
    return _categorical_score(
        value,
        {
            "0": 0.0,
            "no": 0.0,
            "none": 0.0,
            "1": 0.5,
            "yes": 0.75,
            "sometimes_not_enough": 0.75,
            "often_not_enough": 1.0,
        },
        field_name="FD2_child_recent_food_insufficiency_unaffordable_last_7_days",
    )


def _expense_difficulty_score(value: Any) -> float:
    return _categorical_score(
        value,
        {
            "1": 0.0,
            "not_at_all_difficult": 0.0,
            "2": 0.25,
            "a_little_difficult": 0.25,
            "3": 0.6,
            "somewhat_difficult": 0.6,
            "4": 1.0,
            "very_difficult": 1.0,
        },
        field_name="SPN4_difficulty_paying_usual_household_expenses_last_2_months",
    )


def _inflation_stress_score(value: Any) -> float:
    return _categorical_score(
        value,
        {
            "1": 0.0,
            "not_at_all_stressed": 0.0,
            "2": 0.25,
            "a_little_stressed": 0.25,
            "3": 0.6,
            "moderately_stressed": 0.6,
            "4": 1.0,
            "very_stressed": 1.0,
        },
        field_name="INFLATE2_stress_from_price_increases_last_2_months",
    )


def _yes_no_score(value: Any) -> float:
    return _categorical_score(
        value,
        {
            "0": 0.0,
            "no": 0.0,
            "false": 0.0,
            "2": 0.0,
            "1": 1.0,
            "yes": 1.0,
            "true": 1.0,
        },
        field_name="yes_no_field",
    )


def _categorical_score(
    value: Any,
    scores: dict[str, float],
    *,
    field_name: str,
) -> float:
    key = str(value).strip().lower()
    if key not in scores:
        raise ValueError(f"unsupported HPS value for {field_name}: {value}")
    return scores[key]


def _max_score(*values: float) -> float:
    return max(values)


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        raise ValueError("policy reaction scores must have positive mass")
    return {policy_id: scores[policy_id] / total for policy_id in POLICY_IDS}


def _parse_float(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean value cannot be parsed as probability")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"cannot parse probability value: {value}") from exc


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
