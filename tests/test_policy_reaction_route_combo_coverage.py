import json

from experiments.policy_reaction_route_combo_coverage import (
    build_policy_reaction_route_combo_candidate_set,
    extract_policy_reaction_route_combo_candidate,
)


def test_build_route_combo_set_creates_four_variants_for_single_route():
    artifact = build_policy_reaction_route_combo_candidate_set(
        combo_id="r2b-lrp-narrowed",
        artifact_id="route-combo-test",
        primary_candidate=_candidate("primary"),
    )

    assert artifact["schema_version"] == "policy-reaction-route-combo-coverage-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["combo_id"] == "r2b-lrp-narrowed"
    assert artifact["secondary_candidate_id"] is None
    assert artifact["candidates"][0]["variant_tag"] == "conservative_bridge"
    json.dumps(artifact, allow_nan=False)


def test_extract_route_combo_candidate_keeps_product_contract_and_secondary_hints():
    artifact = build_policy_reaction_route_combo_candidate_set(
        combo_id="r3c-latent-prototype",
        artifact_id="route-combo-test",
        primary_candidate=_candidate("primary"),
        secondary_candidate=_candidate("secondary"),
    )
    candidate = extract_policy_reaction_route_combo_candidate(
        artifact,
        candidate_id="route-combo-test-v03",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "route_combo_coverage_candidate_builder"
    prompts = candidate["candidate_prompt_components"]["segment_prompt"]
    anchors = candidate["candidate_prompt_components"]["calibration_anchor"]
    assert "income_band=low" in prompts
    assert "price_stress_level=high" in prompts
    assert "ROUTE-COMBO" in anchors["fixed_income_inflation_stressed"]
    assert "secondary-candidate" in anchors["fixed_income_inflation_stressed"]
    json.dumps(candidate, allow_nan=False)


def _candidate(candidate_id: str) -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": f"{candidate_id}-candidate",
        "generator": "test_generator",
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout_required",
        },
        "best_candidate": {
            "candidate_index": 1,
            "segment": "fixed_income_inflation_stressed",
            "policy_id": "food_subsidy_expansion",
            "proxy_score": 4.254466026348,
            "parameter_patches": [
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "prior_anchor_strength",
                    "parameter_value": 0.59,
                    "parameter_bounds": {"min": 0.45, "max": 0.85},
                },
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.92,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": f"{candidate_id} base prompt.",
                "income_band=low": f"{candidate_id} low-income prompt.",
                "price_stress_level=high": f"{candidate_id} high-price prompt.",
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": f"{candidate_id} base anchor.",
                "income_band=low": f"{candidate_id} low-income anchor.",
                "price_stress_level=high": f"{candidate_id} high-price anchor.",
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }
