import json

from experiments.policy_reaction_lcdu_l1 import (
    build_policy_reaction_lcdu_l1_refinement_set,
    extract_policy_reaction_lcdu_l1_candidate,
)


def test_build_lcdu_l1_refinement_set_creates_l04_neighborhood():
    artifact = build_policy_reaction_lcdu_l1_refinement_set(
        base_candidate=_base_candidate(),
        artifact_id="lcdu-l1-test",
    )

    assert artifact["schema_version"] == "policy-reaction-lcdu-refinement-set-v1"
    assert artifact["candidate_count"] == 4
    assert [candidate["candidate_id"] for candidate in artifact["candidates"]] == [
        "lcdu-l1-test-r01",
        "lcdu-l1-test-r02",
        "lcdu-l1-test-r03",
        "lcdu-l1-test-r04",
    ]
    assert artifact["candidates"][1]["constraint_program"][1]["constraint_type"] == "primary_policy_floor"
    json.dumps(artifact, allow_nan=False)


def test_extract_lcdu_l1_candidate_is_product_compatible():
    candidate_set = build_policy_reaction_lcdu_l1_refinement_set(
        base_candidate=_base_candidate(),
        artifact_id="lcdu-l1-test",
    )
    candidate = extract_policy_reaction_lcdu_l1_candidate(
        candidate_set,
        candidate_id="lcdu-l1-test-r03",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "lcdu_l1_l04_refinement"
    anchor = candidate["candidate_prompt_components"]["calibration_anchor"][
        "fixed_income_inflation_stressed"
    ]
    assert "LCDU-L1" in anchor
    assert "gap(" in anchor
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-lcdu-l0-current-001-l04",
        "generator": "lcdu_l0_latent_constraint_compiler",
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
                    "parameter_value": 0.593211730696,
                    "parameter_bounds": {"min": 0.45, "max": 0.85},
                    "provenance": {
                        "latent_state_updates": {
                            "household_cost_pressure": 0.06,
                            "institutional_trust": -0.12,
                            "policy_relief_urgency": 0.0,
                        },
                        "constraint_program": [
                            {
                                "constraint_type": "distribution_smoothness",
                                "max_top1_probability": 0.5,
                            },
                            {
                                "constraint_type": "segment_rank_guard",
                                "guard": "retain_current_ordering_bias",
                            },
                        ],
                    },
                },
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.927811730696,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
                    "provenance": {
                        "latent_state_updates": {
                            "household_cost_pressure": 0.06,
                            "institutional_trust": -0.12,
                            "policy_relief_urgency": 0.0,
                        },
                        "constraint_program": [
                            {
                                "constraint_type": "distribution_smoothness",
                                "max_top1_probability": 0.5,
                            },
                            {
                                "constraint_type": "segment_rank_guard",
                                "guard": "retain_current_ordering_bias",
                            },
                        ],
                    },
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "Use calibrated parameters."
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "lcdu-l0 candidate"
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }
