import json

from experiments.policy_reaction_s2pc_c01_sparse_subset import (
    build_policy_reaction_s2pc_c01_sparse_subset_set,
    extract_policy_reaction_s2pc_c01_sparse_subset_candidate,
)


def test_build_c01_sparse_subset_set_creates_factor_subsets():
    artifact = build_policy_reaction_s2pc_c01_sparse_subset_set(
        base_candidate=_base_candidate(),
        artifact_id="s2pc-c01-sparse-subset-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-sparse-subset-set-v1"
    assert artifact["candidate_count"] == 3
    assert [item["variant_tag"] for item in artifact["candidates"]] == [
        "household_only",
        "trust_only",
        "core_pair_only",
    ]
    json.dumps(artifact, allow_nan=False)


def test_extract_c01_sparse_subset_candidate_is_product_compatible():
    subset_set = build_policy_reaction_s2pc_c01_sparse_subset_set(
        base_candidate=_base_candidate(),
        artifact_id="s2pc-c01-sparse-subset-test",
    )
    candidate = extract_policy_reaction_s2pc_c01_sparse_subset_candidate(
        subset_set,
        candidate_id="s2pc-c01-sparse-subset-test-s02",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["candidate_id"] == "s2pc-c01-sparse-subset-test-s02"
    assert candidate["generator"] == "s2pc_c01_sparse_factor_subset"
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-s2pc-l1-candidate-set-current-001-c01",
        "generator": "s2pc_l1_multi_candidate_runtime_search",
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
                    "factor_id": "household_budget_rigidity",
                    "parameter_name": "household_budget_rigidity",
                    "parameter_value": 0.130958798022,
                    "parameter_bounds": {"min": 0.0, "max": 0.3},
                    "expected_effect": {"food_subsidy_expansion": "increase"},
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                },
                {
                    "factor_id": "household_budget_rigidity",
                    "parameter_name": "response_temperature",
                    "parameter_value": 0.852785264359,
                    "parameter_bounds": {"min": 0.7, "max": 1.05},
                    "expected_effect": {"food_subsidy_expansion": "increase"},
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                },
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
