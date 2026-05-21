import json

from experiments.policy_reaction_lrp_round1_l0 import (
    build_policy_reaction_lrp_round1_l0_candidate_set,
    extract_policy_reaction_lrp_round1_l0_candidate,
)


def test_build_lrp_round1_l0_candidate_set_generates_four_stronger_families():
    artifact = build_policy_reaction_lrp_round1_l0_candidate_set(
        base_candidate=_base_candidate(),
        axis_weakness=_axis_weakness(),
        artifact_id="lrp-round1-l0-test",
    )
    assert artifact["schema_version"] == "policy-reaction-lrp-candidate-set-v1"
    assert artifact["generator"] == "lrp_round1_l0_latent_response_program_compiler"
    assert artifact["candidate_family"] == "lrp_round1_l0"
    assert artifact["candidate_count"] == 4
    assert [item["candidate_id"] for item in artifact["candidates"]] == [
        "lrp-round1-l0-test-r01",
        "lrp-round1-l0-test-r02",
        "lrp-round1-l0-test-r03",
        "lrp-round1-l0-test-r04",
    ]
    assert artifact["candidates"][2]["latent_response_program"]["response_constraints"][-1] == {
        "constraint_type": "baseline_cap",
        "policy_id": "baseline_no_new_support",
        "max_probability": 0.235,
    }
    json.dumps(artifact, allow_nan=False)


def test_extract_lrp_round1_l0_candidate_keeps_candidate_contract_and_dual_axis_prompts():
    artifact = build_policy_reaction_lrp_round1_l0_candidate_set(
        base_candidate=_base_candidate(),
        axis_weakness=_axis_weakness(),
        artifact_id="lrp-round1-l0-test",
    )
    candidate = extract_policy_reaction_lrp_round1_l0_candidate(
        artifact,
        candidate_id="lrp-round1-l0-test-r03",
    )
    prompts = candidate["candidate_prompt_components"]["segment_prompt"]
    anchors = candidate["candidate_prompt_components"]["calibration_anchor"]
    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert "income_band=low" in prompts
    assert "price_stress_level=high" in prompts
    assert "LRP-R1-L0" in anchors["fixed_income_inflation_stressed"]
    assert "total_rule_strength" in candidate["best_candidate"]["parameter_patches"][0]["provenance"]
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-s2pc-base-001",
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
            "proxy_score": 4.0,
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
                    "parameter_value": 0.93,
                    "parameter_bounds": {"min": 0.80, "max": 1.20},
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "base segment prompt",
                "income_band=low": "low-income selector prompt",
                "price_stress_level=high": "high-price selector prompt",
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "base anchor",
                "income_band=low": "low anchor",
                "price_stress_level=high": "high anchor",
            },
            "response_contract": "strict json",
        },
    }


def _axis_weakness() -> dict:
    return {
        "schema_version": "policy-reaction-axis-weakness-v1",
        "artifact_id": "policy-reaction-axis-weakness-current-001",
        "persistent_weakness": {
            "worst_rank_segment": "income_band=low",
            "worst_jsd_segment": "price_stress_level=high",
        },
    }
