import json

from experiments.policy_reaction_constraint_program_l0 import (
    build_policy_reaction_constraint_program_l0_candidate_set,
    extract_policy_reaction_constraint_program_l0_candidate,
)


def test_build_constraint_program_l0_candidate_set_creates_population_level_family():
    artifact = build_policy_reaction_constraint_program_l0_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="constraint-program-l0-test",
    )

    assert artifact["schema_version"] == "policy-reaction-constraint-program-l0-candidate-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["population_constraint_schema"] == [
        "baseline_share_cap",
        "relief_share_floor",
        "target_gap_band",
        "segment_guard",
    ]
    first = artifact["candidates"][0]
    assert first["population_constraint_program"]["population_latents"]["relief_activation"] == 0.16
    assert first["population_constraint_program"]["population_constraints"][0]["constraint_type"] == "baseline_share_cap"
    assert first["population_constraint_program"]["segment_adjustments"][0]["selector"] == "income_band=low"
    json.dumps(artifact, allow_nan=False)


def test_extract_constraint_program_l0_candidate_is_product_compatible():
    artifact = build_policy_reaction_constraint_program_l0_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="constraint-program-l0-test",
    )
    candidate = extract_policy_reaction_constraint_program_l0_candidate(
        artifact,
        candidate_id="constraint-program-l0-test-c03",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "constraint_program_l0_population_compiler"
    anchor = candidate["candidate_prompt_components"]["calibration_anchor"][
        "working_family_price_stressed"
    ]
    assert "CP-L0" in anchor
    assert "population_latents=" in anchor
    assert "population_constraints=" in anchor
    assert "price_stress_level=high" in anchor
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-lcdu-l3-current-001-i01",
        "generator": "lcdu_l3_dual_axis_guard_family",
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout_required",
        },
        "best_candidate": {
            "candidate_index": 1,
            "segment": "working_family_price_stressed",
            "policy_id": "cash_cost_of_living_rebate",
            "proxy_score": 4.018204160517,
            "parameter_patches": [
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "prior_anchor_strength",
                    "parameter_value": 0.602,
                    "parameter_bounds": {"min": 0.45, "max": 0.85},
                },
                {
                    "factor_id": "household_cost_pressure",
                    "parameter_name": "price_salience_multiplier",
                    "parameter_value": 1.041,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
                },
                {
                    "factor_id": "policy_relief_urgency",
                    "parameter_name": "relief_bias",
                    "parameter_value": 0.318,
                    "parameter_bounds": {"min": 0.15, "max": 0.5},
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "working_family_price_stressed": "Base working-family prompt.",
                "low_income_food_insecure": "Base low-income prompt.",
            },
            "calibration_anchor": {
                "working_family_price_stressed": "Base working-family anchor.",
                "low_income_food_insecure": "Base low-income anchor.",
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }
