"""Semantic-Structured Persona Calibration (S2PC) primitives."""

from __future__ import annotations

import json
import math
from typing import Any


S2PC_SCHEMA_VERSION = "circe-s2pc-v1"
S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
S2PC_GATE_SCHEMA_VERSION = "policy-reaction-s2pc-gate-v1"
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"


def default_semantic_factor_catalog() -> dict[str, Any]:
    factors = [
        _factor(
            "food_insecurity_salience",
            "食品不安全显著性",
            segment_hints=["low_income_food_insecure"],
            policy_hints=["food_subsidy_expansion"],
            parameter_bounds={
                "food_subsidy_expansion_bias": {"min": 0.0, "max": 0.25},
                "semantic_salience_weight": {"min": 0.0, "max": 0.30},
            },
            expected_policy_effect={"food_subsidy_expansion": "increase"},
        ),
        _factor(
            "cash_liquidity_preference",
            "现金流动性偏好",
            segment_hints=[
                "working_family_price_stressed",
                "fixed_income_inflation_stressed",
            ],
            policy_hints=["cash_cost_of_living_rebate"],
            parameter_bounds={
                "cash_cost_of_living_rebate_bias": {"min": 0.0, "max": 0.25},
                "benefit_immediacy_weight": {"min": 0.0, "max": 0.20},
            },
            expected_policy_effect={"cash_cost_of_living_rebate": "increase"},
        ),
        _factor(
            "benefit_immediacy",
            "即时收益偏好",
            segment_hints=[
                "low_income_food_insecure",
                "working_family_price_stressed",
            ],
            policy_hints=["cash_cost_of_living_rebate", "food_subsidy_expansion"],
            parameter_bounds={
                "benefit_immediacy_weight": {"min": 0.0, "max": 0.20},
                "prior_anchor_strength": {"min": 0.50, "max": 0.85},
            },
            expected_policy_effect={
                "cash_cost_of_living_rebate": "increase",
                "food_subsidy_expansion": "increase",
            },
        ),
        _factor(
            "eligibility_uncertainty",
            "资格不确定性",
            segment_hints=[
                "general_population_cost_pressure",
                "working_family_price_stressed",
            ],
            policy_hints=["food_subsidy_expansion"],
            parameter_bounds={
                "eligibility_uncertainty_penalty": {"min": 0.0, "max": 0.20},
                "policy_complexity_aversion": {"min": 0.0, "max": 0.20},
            },
            expected_policy_effect={"food_subsidy_expansion": "decrease"},
        ),
        _factor(
            "institutional_trust",
            "制度信任",
            segment_hints=[
                "general_population_cost_pressure",
                "fixed_income_inflation_stressed",
            ],
            policy_hints=["cash_cost_of_living_rebate", "food_subsidy_expansion"],
            parameter_bounds={
                "trust_multiplier": {"min": 0.80, "max": 1.20},
                "prior_anchor_strength": {"min": 0.45, "max": 0.85},
            },
            expected_policy_effect={
                "cash_cost_of_living_rebate": "increase",
                "food_subsidy_expansion": "increase",
            },
        ),
        _factor(
            "household_budget_rigidity",
            "家庭预算刚性",
            segment_hints=[
                "fixed_income_inflation_stressed",
                "low_income_food_insecure",
            ],
            policy_hints=["cash_cost_of_living_rebate", "food_subsidy_expansion"],
            parameter_bounds={
                "household_budget_rigidity": {"min": 0.0, "max": 0.30},
                "response_temperature": {"min": 0.70, "max": 1.05},
            },
            expected_policy_effect={
                "cash_cost_of_living_rebate": "increase",
                "food_subsidy_expansion": "increase",
            },
        ),
        _factor(
            "policy_complexity_aversion",
            "政策复杂性厌恶",
            segment_hints=[
                "general_population_cost_pressure",
                "working_family_price_stressed",
            ],
            policy_hints=["food_subsidy_expansion"],
            parameter_bounds={
                "policy_complexity_aversion": {"min": 0.0, "max": 0.25},
                "response_temperature": {"min": 0.75, "max": 1.10},
            },
            expected_policy_effect={"food_subsidy_expansion": "decrease"},
        ),
        _factor(
            "inflation_stress_sensitivity",
            "通胀压力敏感度",
            segment_hints=[
                "fixed_income_inflation_stressed",
                "general_population_cost_pressure",
            ],
            policy_hints=["cash_cost_of_living_rebate"],
            parameter_bounds={
                "cash_cost_of_living_rebate_bias": {"min": 0.0, "max": 0.20},
                "inflation_stress_weight": {"min": 0.0, "max": 0.30},
            },
            expected_policy_effect={"cash_cost_of_living_rebate": "increase"},
        ),
    ]
    catalog = {
        "schema_version": S2PC_SCHEMA_VERSION,
        "factor_count": len(factors),
        "factors": factors,
        "claim_boundary": (
            "S2PC semantic factor catalog is a bounded method component, "
            "not a social-science truth claim."
        ),
    }
    validate_semantic_factor_catalog(catalog)
    return catalog


def validate_semantic_factor_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("schema_version") != S2PC_SCHEMA_VERSION:
        raise ValueError("semantic factor catalog has unsupported schema_version")
    factors = catalog.get("factors")
    if not isinstance(factors, list) or not factors:
        raise ValueError("semantic factor catalog requires non-empty factors")
    if catalog.get("factor_count") != len(factors):
        raise ValueError("semantic factor catalog factor_count mismatch")
    seen: set[str] = set()
    for factor in factors:
        factor_id = _required_string(factor, "factor_id")
        if factor_id in seen:
            raise ValueError(f"duplicate semantic factor: {factor_id}")
        seen.add(factor_id)
        _required_string(factor, "label")
        _required_string(factor, "claim_boundary")
        for field_name in ("segment_hints", "policy_hints"):
            values = factor.get(field_name)
            if not isinstance(values, list) or not all(
                isinstance(value, str) and value for value in values
            ):
                raise ValueError(
                    f"{factor_id}.{field_name} must be a non-empty string list"
                )
        bounds = factor.get("parameter_bounds")
        if not isinstance(bounds, dict) or not bounds:
            raise ValueError(
                f"{factor_id}.parameter_bounds must be a non-empty object"
            )
        for parameter_name, parameter_bounds in bounds.items():
            _required_string({"parameter_name": parameter_name}, "parameter_name")
            if not isinstance(parameter_bounds, dict):
                raise ValueError(
                    f"{factor_id}.{parameter_name} bounds must be an object"
                )
            lower = _finite_number(
                parameter_bounds.get("min"),
                f"{factor_id}.{parameter_name}.min",
            )
            upper = _finite_number(
                parameter_bounds.get("max"),
                f"{factor_id}.{parameter_name}.max",
            )
            if lower > upper:
                raise ValueError(f"{factor_id}.{parameter_name} min cannot exceed max")
    _assert_strict_json(catalog)


def _factor(
    factor_id: str,
    label: str,
    *,
    segment_hints: list[str],
    policy_hints: list[str],
    parameter_bounds: dict[str, dict[str, float]],
    expected_policy_effect: dict[str, str],
) -> dict[str, Any]:
    return {
        "factor_id": factor_id,
        "label": label,
        "segment_hints": segment_hints,
        "policy_hints": policy_hints,
        "parameter_bounds": parameter_bounds,
        "expected_policy_effect": expected_policy_effect,
        "claim_boundary": (
            "Semantic factor is used as bounded calibration search metadata, "
            "not as causal proof."
        ),
    }


def _required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} is required")
    return value


def _finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)
