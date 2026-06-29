import json

from experiments.policy_reaction_segment_program_l0 import (
    build_policy_reaction_segment_program_l0_candidate_set,
    extract_policy_reaction_segment_program_candidate,
)


def test_build_segment_program_l0_candidate_set_creates_four_synchronized_families():
    artifact = build_policy_reaction_segment_program_l0_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="segment-program-l0-test",
    )

    assert artifact["schema_version"] == "policy-reaction-segment-program-l0-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["generator"] == "segment_program_l0_family_builder"
    assert artifact["program_axes"] == [
        "soft_guard",
        "qualitative_anchor",
        "cross_segment_transfer",
        "numeric_anchor",
    ]
    third = artifact["candidates"][2]
    selectors = [
        item["selector"]
        for item in third["synchronized_program"]["synchronized_segments"]
    ]
    assert third["variant_tag"] == "segment_crossover_family"
    assert "working_family_price_stressed" in selectors
    assert "income_band=low" in selectors
    json.dumps(artifact, allow_nan=False)


def test_extract_segment_program_candidate_keeps_product_contract_and_sync_prompts():
    artifact = build_policy_reaction_segment_program_l0_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="segment-program-l0-test",
    )
    candidate = extract_policy_reaction_segment_program_candidate(
        artifact,
        candidate_id="segment-program-l0-test-s04",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "segment_program_l0_family_builder"
    prompts = candidate["candidate_prompt_components"]["segment_prompt"]
    anchors = candidate["candidate_prompt_components"]["calibration_anchor"]
    assert "working_family_price_stressed" in prompts
    assert "price_stress_level=high" in prompts
    assert "SEGMENT-PROGRAM-L0" in anchors["fixed_income_inflation_stressed"]
    assert "anchor_heavy" in anchors["working_family_price_stressed"]
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
