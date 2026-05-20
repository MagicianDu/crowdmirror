import json

from experiments.policy_reaction_s2pc_c01_neighborhood import (
    build_policy_reaction_s2pc_c01_neighborhood_set,
    extract_policy_reaction_s2pc_c01_neighborhood_candidate,
    write_policy_reaction_s2pc_c01_neighborhood_candidate,
)


def test_build_c01_neighborhood_set_creates_local_variants():
    artifact = build_policy_reaction_s2pc_c01_neighborhood_set(
        base_candidate=_base_candidate(),
        artifact_id="s2pc-c01-neighborhood-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-neighborhood-set-v1"
    assert artifact["artifact_id"] == "s2pc-c01-neighborhood-test"
    assert artifact["generator"] == "s2pc_c01_local_neighborhood_search"
    assert artifact["candidate_count"] == 3
    assert [item["candidate_id"] for item in artifact["candidates"]] == [
        "s2pc-c01-neighborhood-test-n01",
        "s2pc-c01-neighborhood-test-n02",
        "s2pc-c01-neighborhood-test-n03",
    ]
    assert all(item["segment"] == "fixed_income_inflation_stressed" for item in artifact["candidates"])
    json.dumps(artifact, allow_nan=False)


def test_extract_c01_neighborhood_candidate_is_product_compatible():
    neighborhood = build_policy_reaction_s2pc_c01_neighborhood_set(
        base_candidate=_base_candidate(),
        artifact_id="s2pc-c01-neighborhood-test",
    )

    candidate = extract_policy_reaction_s2pc_c01_neighborhood_candidate(
        neighborhood,
        candidate_id="s2pc-c01-neighborhood-test-n02",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "s2pc_c01_local_neighborhood_search"
    assert candidate["candidate_id"] == "s2pc-c01-neighborhood-test-n02"
    assert candidate["candidate_prompt_components"]["calibration_anchor"]
    json.dumps(candidate, allow_nan=False)


def test_write_c01_neighborhood_candidate(tmp_path):
    base_candidate_path = tmp_path / "base.json"
    neighborhood_path = tmp_path / "neighborhood.json"
    output = tmp_path / "candidate.json"
    base_candidate_path.write_text(json.dumps(_base_candidate()))
    neighborhood = build_policy_reaction_s2pc_c01_neighborhood_set(
        base_candidate=_base_candidate(),
        artifact_id="s2pc-c01-neighborhood-test",
    )
    neighborhood_path.write_text(json.dumps(neighborhood))

    written = write_policy_reaction_s2pc_c01_neighborhood_candidate(
        output,
        neighborhood_set_path=neighborhood_path,
        candidate_id="s2pc-c01-neighborhood-test-n01",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["candidate_id"] == "s2pc-c01-neighborhood-test-n01"


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
                    "factor_label": "家庭预算刚性",
                    "parameter_name": "household_budget_rigidity",
                    "parameter_value": 0.130958798022,
                    "parameter_bounds": {"min": 0.0, "max": 0.3},
                    "expected_effect": {
                        "cash_cost_of_living_rebate": "increase",
                        "food_subsidy_expansion": "increase",
                    },
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                    "provenance": {"source_split": "calibration"},
                },
                {
                    "factor_id": "household_budget_rigidity",
                    "factor_label": "家庭预算刚性",
                    "parameter_name": "response_temperature",
                    "parameter_value": 0.852785264359,
                    "parameter_bounds": {"min": 0.7, "max": 1.05},
                    "expected_effect": {
                        "cash_cost_of_living_rebate": "increase",
                        "food_subsidy_expansion": "increase",
                    },
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                    "provenance": {"source_split": "calibration"},
                },
                {
                    "factor_id": "institutional_trust",
                    "factor_label": "制度信任",
                    "parameter_name": "prior_anchor_strength",
                    "parameter_value": 0.624611730696,
                    "parameter_bounds": {"min": 0.45, "max": 0.85},
                    "expected_effect": {
                        "cash_cost_of_living_rebate": "increase",
                        "food_subsidy_expansion": "increase",
                    },
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                    "provenance": {"source_split": "calibration"},
                },
                {
                    "factor_id": "institutional_trust",
                    "factor_label": "制度信任",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.974611730696,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
                    "expected_effect": {
                        "cash_cost_of_living_rebate": "increase",
                        "food_subsidy_expansion": "increase",
                    },
                    "policy_id": "food_subsidy_expansion",
                    "segment": "fixed_income_inflation_stressed",
                    "provenance": {"source_split": "calibration"},
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "Use the persona's calibrated policy-reaction parameters when estimating support probabilities for this segment."
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "S2PC factors=household_budget_rigidity,institutional_trust; primary_policy=food_subsidy_expansion; parameters=household_budget_rigidity=0.130958798022;response_temperature=0.852785264359;prior_anchor_strength=0.624611730696;trust_multiplier=0.974611730696"
            },
            "response_contract": "Return strict JSON probabilities over the available policy alternatives.",
        },
    }
