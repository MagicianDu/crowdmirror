import json

from circe.calibration.s2pc import (
    S2PC_SCHEMA_VERSION,
    default_semantic_factor_catalog,
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
