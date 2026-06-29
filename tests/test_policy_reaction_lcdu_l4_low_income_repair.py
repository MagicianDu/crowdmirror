import json

from experiments.policy_reaction_lcdu_l4_low_income_repair import (
    build_policy_reaction_lcdu_l4_low_income_repair_set,
    extract_policy_reaction_lcdu_l4_low_income_repair_candidate,
)


def test_build_lcdu_l4_low_income_repair_set_creates_candidates():
    artifact = build_policy_reaction_lcdu_l4_low_income_repair_set(
        base_candidate=_base_candidate(),
        residual_weakness=_residual_weakness(),
        artifact_id="lcdu-l4-repair-test",
    )

    assert artifact["schema_version"] == "policy-reaction-lcdu-repair-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["segment_id"] == "low_income_food_insecure"
    assert "raise cash_cost_of_living_rebate" in artifact["repair_direction"]
    json.dumps(artifact, allow_nan=False)


def test_extract_lcdu_l4_low_income_candidate_is_product_compatible():
    candidate_set = build_policy_reaction_lcdu_l4_low_income_repair_set(
        base_candidate=_base_candidate(),
        residual_weakness=_residual_weakness(),
        artifact_id="lcdu-l4-repair-test",
    )
    candidate = extract_policy_reaction_lcdu_l4_low_income_repair_candidate(
        candidate_set,
        candidate_id="lcdu-l4-repair-test-r02",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "lcdu_l4_low_income_repair_family"
    prompt = candidate["candidate_prompt_components"]["segment_prompt"][
        "low_income_food_insecure"
    ]
    anchor = candidate["candidate_prompt_components"]["calibration_anchor"][
        "low_income_food_insecure"
    ]
    assert "cash_cost_of_living_rebate" in prompt
    assert "min_cash_rebate_probability=0.305" in anchor
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-lcdu-l3-current-001-h02",
        "generator": "lcdu_l3_working_family_guard_family",
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
                }
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "Use the persona's calibrated policy-reaction parameters for this segment."
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "LCDU-L3 factors=institutional_trust"
            },
            "response_contract": "Return strict JSON probabilities over the available policy alternatives.",
        },
    }


def _residual_weakness() -> dict:
    return {
        "schema_version": "policy-reaction-lcdu-residual-weakness-v1",
        "artifact_id": "weakness-test",
        "segment_id": "low_income_food_insecure",
        "weakness_summary": {
            "recommended_repair_direction": (
                "raise cash_cost_of_living_rebate while trimming baseline_no_new_support "
                "and lightly trimming food_subsidy_expansion for low_income_food_insecure"
            )
        },
    }
