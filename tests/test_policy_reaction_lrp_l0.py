import json

from experiments.policy_reaction_lrp_l0 import (
    build_policy_reaction_lrp_l0_candidate_set,
    extract_policy_reaction_lrp_candidate,
)


def test_build_lrp_l0_candidate_set_creates_program_level_candidates():
    artifact = build_policy_reaction_lrp_l0_candidate_set(
        base_candidate=_base_candidate(),
        axis_weakness=_axis_weakness(),
        artifact_id="lrp-l0-test",
    )

    assert artifact["schema_version"] == "policy-reaction-lrp-candidate-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["latent_response_schema"] == [
        "baseline_inertia",
        "relief_preference",
        "price_stress_reactivity",
        "targeting_sensitivity",
    ]
    first = artifact["candidates"][0]
    assert first["latent_response_program"]["regime_rules"][0]["selector"] == "income_band=low"
    assert first["latent_response_program"]["response_constraints"][0]["constraint_type"] == "rank_guard"
    json.dumps(artifact, allow_nan=False)


def test_extract_lrp_candidate_is_product_compatible_and_keeps_regime_selectors():
    artifact = build_policy_reaction_lrp_l0_candidate_set(
        base_candidate=_base_candidate(),
        axis_weakness=_axis_weakness(),
        artifact_id="lrp-l0-test",
    )
    candidate = extract_policy_reaction_lrp_candidate(
        artifact,
        candidate_id="lrp-l0-test-p03",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "lrp_l0_latent_response_program_compiler"
    prompts = candidate["candidate_prompt_components"]["segment_prompt"]
    anchors = candidate["candidate_prompt_components"]["calibration_anchor"]
    assert "income_band=low" in prompts
    assert "price_stress_level=high" in prompts
    assert "income_band=low" in anchors
    assert "price_stress_level=high" in anchors
    assert "LRP-L0" in anchors["fixed_income_inflation_stressed"]
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
                "fixed_income_inflation_stressed": "Base fixed-income prompt.",
                "working_family_price_stressed": "Base working-family prompt.",
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "Base fixed-income anchor.",
                "working_family_price_stressed": "Base working-family anchor.",
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }


def _axis_weakness() -> dict:
    return {
        "schema_version": "policy-reaction-axis-weakness-v1",
        "artifact_id": "policy-reaction-axis-weakness-lcdu-l3-current-001",
        "persistent_weakness": {
            "worst_jsd_segment": "price_stress_level=high",
            "worst_jsd_value_mean": 0.14925228029562396,
            "worst_rank_segment": "income_band=low",
            "worst_rank_value_mean": -1.0,
        },
    }
