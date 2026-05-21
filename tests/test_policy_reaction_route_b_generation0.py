import json

from experiments.policy_reaction_route_b_generation0 import (
    build_policy_reaction_route_b_generation0_candidate_set,
    extract_policy_reaction_route_b_candidate,
)


def test_build_route_b_generation0_candidate_set_creates_small_population():
    artifact = build_policy_reaction_route_b_generation0_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="route-b-generation0-test",
    )

    assert artifact["schema_version"] == "policy-reaction-route-b-candidate-set-v1"
    assert artifact["candidate_count"] == 4
    assert [item["variant_tag"] for item in artifact["candidates"]] == [
        "anchor_down_multiplier_down",
        "anchor_down_multiplier_hold",
        "anchor_hold_multiplier_down",
        "anchor_mid_multiplier_mid",
    ]
    json.dumps(artifact, allow_nan=False)


def test_extract_route_b_candidate_is_product_compatible():
    candidate_set = build_policy_reaction_route_b_generation0_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="route-b-generation0-test",
    )
    candidate = extract_policy_reaction_route_b_candidate(
        candidate_set,
        candidate_id="route-b-generation0-test-g03",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["candidate_id"] == "route-b-generation0-test-g03"
    assert candidate["generator"] == "route_b_generation0_small_population_search"
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-s2pc-c01-sparse-subset-current-001-s02",
        "generator": "s2pc_c01_sparse_factor_subset",
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
                    "parameter_value": 0.624611730696,
                    "parameter_bounds": {"min": 0.45, "max": 0.85},
                },
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.974611730696,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "Use calibrated parameters."
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "trust candidate"
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }
