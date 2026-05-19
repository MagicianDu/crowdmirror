import json

import pytest

from circe.calibration.s2pc import (
    S2PC_SCHEMA_VERSION,
    default_semantic_factor_catalog,
    mine_policy_reaction_residuals,
    validate_semantic_factor_catalog,
)


def test_default_semantic_factor_catalog_is_strict_json_and_bounded():
    catalog = default_semantic_factor_catalog()

    assert catalog["schema_version"] == S2PC_SCHEMA_VERSION
    assert catalog["factor_count"] == 8
    assert {
        factor["factor_id"] for factor in catalog["factors"]
    } == {
        "food_insecurity_salience",
        "cash_liquidity_preference",
        "benefit_immediacy",
        "eligibility_uncertainty",
        "institutional_trust",
        "household_budget_rigidity",
        "policy_complexity_aversion",
        "inflation_stress_sensitivity",
    }
    for factor in catalog["factors"]:
        assert factor["claim_boundary"]
        assert factor["parameter_bounds"]
        for parameter_name, bounds in factor["parameter_bounds"].items():
            assert set(bounds) == {"min", "max"}
            assert bounds["min"] <= bounds["max"], parameter_name

    validate_semantic_factor_catalog(catalog)
    json.dumps(catalog, allow_nan=False)


def test_mine_policy_reaction_residuals_uses_only_calibration_split():
    residuals = mine_policy_reaction_residuals(_calibration_benchmark())

    assert residuals["schema_version"] == "circe-s2pc-residuals-v1"
    assert residuals["source_split"] == "calibration"
    assert residuals["residual_count"] == 6
    first = residuals["residuals"][0]
    assert first == {
        "segment": "general_population_cost_pressure",
        "policy_id": "baseline_no_new_support",
        "official_probability": 0.55,
        "predicted_probability": 0.10,
        "residual": 0.45,
        "direction": "under_predicted",
        "magnitude": 0.45,
    }
    json.dumps(residuals, allow_nan=False)


def test_mine_policy_reaction_residuals_rejects_heldout_generation():
    artifact = _calibration_benchmark()
    artifact["source_ingestion_artifact_id"] = (
        "policy-reaction-htops-evaluation-ingestion"
    )

    with pytest.raises(ValueError, match="calibration split"):
        mine_policy_reaction_residuals(artifact)


def _calibration_benchmark() -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": "policy-reaction-calibration-benchmark-test",
        "source_ingestion_artifact_id": "policy-reaction-htops-calibration-ingestion",
        "prediction_artifact_id": "policy-reaction-initial-predictions-test",
        "overall_status": "passed",
        "benchmark_metrics": {"weighted_choice_distribution_jsd": 0.20},
        "segment_coverage": {"coverage_rate": 1.0},
        "segment_metrics": {
            "low_income_food_insecure": {
                "official_distribution": {
                    "baseline_no_new_support": 0.20,
                    "cash_cost_of_living_rebate": 0.25,
                    "food_subsidy_expansion": 0.55,
                },
                "predicted_distribution": {
                    "baseline_no_new_support": 0.05,
                    "cash_cost_of_living_rebate": 0.35,
                    "food_subsidy_expansion": 0.60,
                },
            },
            "general_population_cost_pressure": {
                "official_distribution": {
                    "baseline_no_new_support": 0.55,
                    "cash_cost_of_living_rebate": 0.27,
                    "food_subsidy_expansion": 0.18,
                },
                "predicted_distribution": {
                    "baseline_no_new_support": 0.10,
                    "cash_cost_of_living_rebate": 0.34,
                    "food_subsidy_expansion": 0.56,
                },
            },
        },
    }
