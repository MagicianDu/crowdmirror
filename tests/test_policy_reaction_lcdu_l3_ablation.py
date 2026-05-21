import json

from experiments.policy_reaction_lcdu_l3_ablation import (
    build_policy_reaction_lcdu_l3_ablation_set,
    extract_policy_reaction_lcdu_l3_ablation_candidate,
)


def test_build_lcdu_l3_ablation_set_creates_explanation_family():
    artifact = build_policy_reaction_lcdu_l3_ablation_set(
        base_candidate=_base_candidate(),
        artifact_id="lcdu-l3-ablation-test",
    )

    assert artifact["schema_version"] == "policy-reaction-lcdu-ablation-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["candidates"][0]["variant_tag"] == "prompt_only_guard"
    assert artifact["candidates"][1]["working_family_prompt_enabled"] is False
    assert artifact["candidates"][2]["working_family_anchor_enabled"] is True
    json.dumps(artifact, allow_nan=False)


def test_extract_lcdu_l3_ablation_candidate_is_product_compatible():
    candidate_set = build_policy_reaction_lcdu_l3_ablation_set(
        base_candidate=_base_candidate(),
        artifact_id="lcdu-l3-ablation-test",
    )
    candidate = extract_policy_reaction_lcdu_l3_ablation_candidate(
        candidate_set,
        candidate_id="lcdu-l3-ablation-test-a02",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "lcdu_l3_ablation_family"
    assert "working_family_price_stressed" not in candidate["candidate_prompt_components"][
        "segment_prompt"
    ]
    assert "working_family_price_stressed" in candidate["candidate_prompt_components"][
        "calibration_anchor"
    ]
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
                "fixed_income_inflation_stressed": "Use the persona's calibrated policy-reaction parameters.",
                "working_family_price_stressed": "Keep this segment near its calibration-split baseline response profile.",
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "LCDU-L3 factors=institutional_trust",
                "working_family_price_stressed": "LCDU-L3 guard_policy=working_family_mid_guard; max_food_subsidy_probability=0.25; min_cash_rebate_probability=0.41",
            },
            "response_contract": "Return strict JSON probabilities over the available policy alternatives.",
        },
    }
