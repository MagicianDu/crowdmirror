import json

from experiments.policy_reaction_lcdu_l3 import (
    build_policy_reaction_lcdu_l3_working_family_guard_set,
    extract_policy_reaction_lcdu_l3_candidate,
)


def test_build_lcdu_l3_guard_set_creates_threshold_family():
    artifact = build_policy_reaction_lcdu_l3_working_family_guard_set(
        base_candidate=_base_candidate(),
        artifact_id="lcdu-l3-test",
    )

    assert artifact["schema_version"] == "policy-reaction-lcdu-segment-guard-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["candidates"][0]["working_family_guard"]["max_food_subsidy_probability"] == 0.255
    assert artifact["candidates"][-1]["working_family_guard"]["min_cash_rebate_probability"] == 0.418
    json.dumps(artifact, allow_nan=False)


def test_extract_lcdu_l3_candidate_is_product_compatible():
    candidate_set = build_policy_reaction_lcdu_l3_working_family_guard_set(
        base_candidate=_base_candidate(),
        artifact_id="lcdu-l3-test",
    )
    candidate = extract_policy_reaction_lcdu_l3_candidate(
        candidate_set,
        candidate_id="lcdu-l3-test-h03",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "lcdu_l3_working_family_guard_family"
    assert "working_family_price_stressed" in candidate["candidate_prompt_components"]["segment_prompt"]
    assert "LCDU-L3" in candidate["candidate_prompt_components"]["calibration_anchor"][
        "working_family_price_stressed"
    ]
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
                },
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.927811730696,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
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
