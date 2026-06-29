import json

from experiments.policy_reaction_s2pc_s02_parameter_subset import (
    build_policy_reaction_s2pc_s02_parameter_subset_set,
    extract_policy_reaction_s2pc_s02_parameter_subset_candidate,
)


def test_build_s02_parameter_subset_set_creates_parameter_variants():
    artifact = build_policy_reaction_s2pc_s02_parameter_subset_set(
        base_candidate=_base_candidate(),
        artifact_id="s2pc-s02-parameter-subset-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-parameter-subset-set-v1"
    assert artifact["candidate_count"] == 2
    assert [item["variant_tag"] for item in artifact["candidates"]] == [
        "prior_anchor_only",
        "trust_multiplier_only",
    ]
    json.dumps(artifact, allow_nan=False)


def test_extract_s02_parameter_subset_candidate_is_product_compatible():
    subset_set = build_policy_reaction_s2pc_s02_parameter_subset_set(
        base_candidate=_base_candidate(),
        artifact_id="s2pc-s02-parameter-subset-test",
    )
    candidate = extract_policy_reaction_s2pc_s02_parameter_subset_candidate(
        subset_set,
        candidate_id="s2pc-s02-parameter-subset-test-p01",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["candidate_id"] == "s2pc-s02-parameter-subset-test-p01"
    assert candidate["generator"] == "s2pc_s02_parameter_subset_search"
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
                    "expected_effect": {"food_subsidy_expansion": "increase"},
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                },
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.974611730696,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
                    "expected_effect": {"food_subsidy_expansion": "increase"},
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                },
            ],
        },
    }
