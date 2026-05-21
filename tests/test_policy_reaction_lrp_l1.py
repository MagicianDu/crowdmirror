import json

from experiments.policy_reaction_lrp_l1 import (
    build_policy_reaction_lrp_l1_candidate_set,
    extract_policy_reaction_lrp_l1_candidate,
)


def test_build_lrp_l1_candidate_set_narrows_to_improved_l0_families():
    artifact = build_policy_reaction_lrp_l1_candidate_set(
        l0_candidate_set=_l0_candidate_set(),
        l0_runtime_matrix=_l0_runtime_matrix(),
        artifact_id="lrp-l1-test",
    )
    assert artifact["schema_version"] == "policy-reaction-lrp-l1-set-v1"
    assert artifact["selected_l0_candidates"] == [
        "policy-reaction-lrp-l0-current-001-p01",
        "policy-reaction-lrp-l0-current-001-p02",
    ]
    assert artifact["candidate_count"] == 4
    assert artifact["candidates"][0]["variant_tag"] == "low_income_milder_compensation"
    json.dumps(artifact, allow_nan=False)


def test_extract_lrp_l1_candidate_keeps_selector_prompts():
    artifact = build_policy_reaction_lrp_l1_candidate_set(
        l0_candidate_set=_l0_candidate_set(),
        l0_runtime_matrix=_l0_runtime_matrix(),
        artifact_id="lrp-l1-test",
    )
    candidate = extract_policy_reaction_lrp_l1_candidate(
        artifact,
        candidate_id="lrp-l1-test-q04",
    )
    prompts = candidate["candidate_prompt_components"]["segment_prompt"]
    anchors = candidate["candidate_prompt_components"]["calibration_anchor"]
    assert "income_band=low" in prompts
    assert "price_stress_level=high" in prompts
    assert "LRP-L1" in anchors["fixed_income_inflation_stressed"]
    json.dumps(candidate, allow_nan=False)


def _l0_candidate_set() -> dict:
    return {
        "schema_version": "policy-reaction-lrp-candidate-set-v1",
        "artifact_id": "policy-reaction-lrp-l0-current-001",
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout_required",
        },
        "candidates": [
            {
                "candidate_id": "policy-reaction-lrp-l0-current-001-p01",
                "candidate_index": 1,
                "segment": "fixed_income_inflation_stressed",
                "policy_id": "food_subsidy_expansion",
                "proxy_score": 4.0,
                "variant_tag": "p01",
                "latent_response_program": {
                    "global_latents": {
                        "baseline_inertia": -0.1,
                        "relief_preference": 0.22,
                        "price_stress_reactivity": 0.04,
                        "targeting_sensitivity": 0.18,
                    },
                    "regime_rules": [
                        {
                            "selector": "income_band=low",
                            "program_intent": "low-income compensation",
                            "latent_delta": {
                                "baseline_inertia": -0.08,
                                "relief_preference": 0.12,
                                "price_stress_reactivity": 0.0,
                                "targeting_sensitivity": 0.10,
                            },
                        }
                    ],
                    "response_constraints": [
                        {
                            "constraint_type": "rank_guard",
                            "selector": "income_band=low",
                            "guard": "support_options_over_baseline",
                        },
                        {
                            "constraint_type": "relief_floor",
                            "policy_id": "cash_cost_of_living_rebate",
                            "min_probability": 0.28,
                        },
                    ],
                },
                "parameter_patches": [
                    {
                        "factor_id": "institutional_trust",
                        "parameter_name": "prior_anchor_strength",
                        "parameter_value": 0.61,
                        "parameter_bounds": {"min": 0.45, "max": 0.85},
                    },
                    {
                        "factor_id": "institutional_trust",
                        "parameter_name": "trust_multiplier",
                        "parameter_value": 0.94,
                        "parameter_bounds": {"min": 0.8, "max": 1.2},
                    },
                ],
                "candidate_prompt_components": {
                    "segment_prompt": {
                        "fixed_income_inflation_stressed": "base",
                        "income_band=low": "low",
                    },
                    "calibration_anchor": {
                        "fixed_income_inflation_stressed": "base anchor",
                        "income_band=low": "low anchor",
                    },
                    "response_contract": "strict json",
                },
            },
            {
                "candidate_id": "policy-reaction-lrp-l0-current-001-p02",
                "candidate_index": 1,
                "segment": "fixed_income_inflation_stressed",
                "policy_id": "food_subsidy_expansion",
                "proxy_score": 4.0,
                "variant_tag": "p02",
                "latent_response_program": {
                    "global_latents": {
                        "baseline_inertia": -0.06,
                        "relief_preference": 0.16,
                        "price_stress_reactivity": 0.24,
                        "targeting_sensitivity": 0.06,
                    },
                    "regime_rules": [
                        {
                            "selector": "price_stress_level=high",
                            "program_intent": "high-price response",
                            "latent_delta": {
                                "baseline_inertia": -0.06,
                                "relief_preference": 0.10,
                                "price_stress_reactivity": 0.14,
                                "targeting_sensitivity": 0.0,
                            },
                        }
                    ],
                    "response_constraints": [
                        {
                            "constraint_type": "distribution_shape_guard",
                            "selector": "price_stress_level=high",
                            "max_baseline_probability": 0.24,
                        },
                        {
                            "constraint_type": "relief_floor",
                            "policy_id": "cash_cost_of_living_rebate",
                            "min_probability": 0.30,
                        },
                    ],
                },
                "parameter_patches": [
                    {
                        "factor_id": "institutional_trust",
                        "parameter_name": "prior_anchor_strength",
                        "parameter_value": 0.60,
                        "parameter_bounds": {"min": 0.45, "max": 0.85},
                    },
                    {
                        "factor_id": "institutional_trust",
                        "parameter_name": "trust_multiplier",
                        "parameter_value": 0.94,
                        "parameter_bounds": {"min": 0.8, "max": 1.2},
                    },
                ],
                "candidate_prompt_components": {
                    "segment_prompt": {
                        "fixed_income_inflation_stressed": "base",
                        "price_stress_level=high": "high",
                    },
                    "calibration_anchor": {
                        "fixed_income_inflation_stressed": "base anchor",
                        "price_stress_level=high": "high anchor",
                    },
                    "response_contract": "strict json",
                },
            },
        ],
    }


def _l0_runtime_matrix() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-matrix-v1",
        "artifact_id": "policy-reaction-lrp-l0-matrix-gpt-oss-20b-12x3-heldout-001",
        "candidate_results": [
            {
                "s2pc_candidate_id": "policy-reaction-lrp-l0-current-001-p01",
                "overall_status": "improved",
            },
            {
                "s2pc_candidate_id": "policy-reaction-lrp-l0-current-001-p02",
                "overall_status": "improved",
            },
            {
                "s2pc_candidate_id": "policy-reaction-lrp-l0-current-001-p03",
                "overall_status": "regressed",
            },
        ],
    }
