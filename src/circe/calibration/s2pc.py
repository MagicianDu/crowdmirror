"""Semantic-Structured Persona Calibration (S2PC) primitives."""

from __future__ import annotations

import json
import math
import copy
from typing import Any


S2PC_SCHEMA_VERSION = "circe-s2pc-v1"
S2PC_CANDIDATE_SCHEMA_VERSION = "policy-reaction-s2pc-candidate-v1"
S2PC_GATE_SCHEMA_VERSION = "policy-reaction-s2pc-gate-v1"
RESIDUAL_SCHEMA_VERSION = "circe-s2pc-residuals-v1"
SEMANTIC_MATCH_SCHEMA_VERSION = "circe-s2pc-semantic-matches-v1"
PARAMETER_PATCH_SCHEMA_VERSION = "circe-s2pc-parameter-patches-v1"
POLICY_REACTION_BENCHMARK_SCHEMA_VERSION = (
    "policy-reaction-official-segment-benchmark-v1"
)
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


def mine_policy_reaction_residuals(
    calibration_benchmark: dict[str, Any],
    *,
    min_magnitude: float = 0.0,
) -> dict[str, Any]:
    _validate_policy_reaction_benchmark(calibration_benchmark, "calibration_benchmark")
    if _source_split(calibration_benchmark) != "calibration":
        raise ValueError("S2PC residual mining requires calibration split")
    residuals = []
    for segment, metrics in sorted(calibration_benchmark["segment_metrics"].items()):
        official = _policy_distribution(
            metrics.get("official_distribution"),
            f"{segment}.official_distribution",
        )
        predicted = _policy_distribution(
            metrics.get("predicted_distribution"),
            f"{segment}.predicted_distribution",
        )
        for policy_id in sorted(set(official) | set(predicted)):
            official_probability = official.get(policy_id, 0.0)
            predicted_probability = predicted.get(policy_id, 0.0)
            residual = round(official_probability - predicted_probability, 12)
            magnitude = round(abs(residual), 12)
            if magnitude < min_magnitude:
                continue
            residuals.append(
                {
                    "segment": segment,
                    "policy_id": policy_id,
                    "official_probability": official_probability,
                    "predicted_probability": predicted_probability,
                    "residual": residual,
                    "direction": _residual_direction(residual),
                    "magnitude": magnitude,
                }
            )
    artifact = {
        "schema_version": RESIDUAL_SCHEMA_VERSION,
        "source_benchmark_artifact_id": calibration_benchmark["artifact_id"],
        "source_prediction_artifact_id": calibration_benchmark.get(
            "prediction_artifact_id"
        ),
        "source_split": "calibration",
        "residual_count": len(residuals),
        "residuals": residuals,
        "claim_boundary": (
            "S2PC residuals are calibration-split candidate-generation evidence only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def retrieve_semantic_factors(
    residual_artifact: dict[str, Any],
    catalog: dict[str, Any],
    *,
    top_k: int = 2,
) -> dict[str, Any]:
    if residual_artifact.get("schema_version") != RESIDUAL_SCHEMA_VERSION:
        raise ValueError("residual_artifact has unsupported schema_version")
    validate_semantic_factor_catalog(catalog)
    if isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be positive")
    matches = []
    for residual in residual_artifact["residuals"]:
        if residual["direction"] == "matched":
            continue
        scored = []
        for factor in catalog["factors"]:
            score = _factor_match_score(residual, factor)
            if score > 0.0:
                scored.append((score, factor))
        for score, factor in sorted(
            scored,
            key=lambda item: (-item[0], item[1]["factor_id"]),
        )[:top_k]:
            matches.append(
                {
                    "segment": residual["segment"],
                    "policy_id": residual["policy_id"],
                    "residual": residual["residual"],
                    "direction": residual["direction"],
                    "magnitude": residual["magnitude"],
                    "factor_id": factor["factor_id"],
                    "factor_label": factor["label"],
                    "score": round(score, 12),
                    "expected_policy_effect": copy.deepcopy(
                        factor["expected_policy_effect"]
                    ),
                    "claim_boundary": factor["claim_boundary"],
                }
            )
    artifact = {
        "schema_version": SEMANTIC_MATCH_SCHEMA_VERSION,
        "source_residual_artifact_id": residual_artifact[
            "source_benchmark_artifact_id"
        ],
        "source_split": "calibration",
        "top_k": top_k,
        "match_count": len(matches),
        "matches": matches,
        "claim_boundary": (
            "S2PC semantic matches are deterministic catalog matches, "
            "not field validation."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def compile_semantic_matches_to_parameter_patches(
    semantic_matches: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    if semantic_matches.get("schema_version") != SEMANTIC_MATCH_SCHEMA_VERSION:
        raise ValueError("semantic_matches has unsupported schema_version")
    validate_semantic_factor_catalog(catalog)
    factors_by_id = {factor["factor_id"]: factor for factor in catalog["factors"]}
    patches = []
    for match in semantic_matches["matches"]:
        factor = factors_by_id[match["factor_id"]]
        for parameter_name, bounds in sorted(factor["parameter_bounds"].items()):
            parameter_value = _parameter_value_for_match(match, bounds)
            patches.append(
                {
                    "segment": match["segment"],
                    "policy_id": match["policy_id"],
                    "factor_id": match["factor_id"],
                    "factor_label": match["factor_label"],
                    "parameter_name": parameter_name,
                    "parameter_value": parameter_value,
                    "parameter_bounds": copy.deepcopy(bounds),
                    "expected_effect": copy.deepcopy(
                        match["expected_policy_effect"]
                    ),
                    "provenance": {
                        "residual": match["residual"],
                        "direction": match["direction"],
                        "magnitude": match["magnitude"],
                        "match_score": match["score"],
                        "source_split": "calibration",
                    },
                }
            )
    artifact = {
        "schema_version": PARAMETER_PATCH_SCHEMA_VERSION,
        "source_split": "calibration",
        "parameter_patch_count": len(patches),
        "parameter_patches": patches,
        "claim_boundary": (
            "S2PC parameter patches are bounded candidate-generation evidence only."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


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


def _factor_match_score(residual: dict[str, Any], factor: dict[str, Any]) -> float:
    score = float(residual["magnitude"])
    if residual["segment"] in factor["segment_hints"]:
        score += 1.0
    if residual["policy_id"] in factor["policy_hints"]:
        score += 1.0
    if (
        residual["segment"] in factor["segment_hints"]
        and residual["policy_id"] in factor["policy_hints"]
        and len(factor["segment_hints"]) == 1
        and len(factor["policy_hints"]) == 1
    ):
        score += 0.25
    expected = factor.get("expected_policy_effect", {}).get(residual["policy_id"])
    if expected == "increase" and residual["direction"] == "under_predicted":
        score += 0.5
    if expected == "decrease" and residual["direction"] == "over_predicted":
        score += 0.5
    return score


def _parameter_value_for_match(
    match: dict[str, Any],
    bounds: dict[str, float],
) -> float:
    lower = float(bounds["min"])
    upper = float(bounds["max"])
    span = upper - lower
    scaled = lower + span * min(1.0, float(match["magnitude"]))
    return round(scaled, 12)


def _validate_policy_reaction_benchmark(
    artifact: dict[str, Any],
    label: str,
) -> None:
    if artifact.get("schema_version") != POLICY_REACTION_BENCHMARK_SCHEMA_VERSION:
        raise ValueError(f"{label} has unsupported schema_version")
    if not artifact.get("artifact_id"):
        raise ValueError(f"{label} missing artifact_id")
    if not isinstance(artifact.get("segment_metrics"), dict):
        raise ValueError(f"{label} missing segment_metrics")


def _source_split(artifact: dict[str, Any]) -> str:
    source = str(artifact.get("source_ingestion_artifact_id", "")).lower()
    if "calibration" in source:
        return "calibration"
    if "evaluation" in source or "heldout" in source or "held-out" in source:
        return "heldout"
    return "unknown"


def _policy_distribution(raw: Any, context: str) -> dict[str, float]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{context} must be a non-empty object")
    values = {}
    for policy_id, value in raw.items():
        values[str(policy_id)] = _non_negative_probability(
            value,
            f"{context}.{policy_id}",
        )
    return values


def _non_negative_probability(value: Any, field_name: str) -> float:
    number = _finite_number(value, field_name)
    if number < 0.0:
        raise ValueError(f"{field_name} must be non-negative")
    return number


def _residual_direction(residual: float) -> str:
    if residual > 0.0:
        return "under_predicted"
    if residual < 0.0:
        return "over_predicted"
    return "matched"


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
